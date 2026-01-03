"""Data coordinator for BIR Waste Watch integration."""

from __future__ import annotations

import datetime as dt
from datetime import datetime, timedelta
import logging
import re
from typing import Any
from urllib.parse import unquote

from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_ADDRESS_SEARCH_URL,
    API_APP_ID,
    API_LOGIN_URL,
    API_PICKUP_URL,
    API_PROVIDER_ID,
    API_TIMEOUT,
    DOMAIN,
    PICKUP_LOOKUP_DAYS,
    SCAN_INTERVAL,
    WASTE_TYPE_MAP,
)

_LOGGER = logging.getLogger(__name__)

# Storage version and key for token persistence
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.tokens"


class BIRTokenStorage:
    """Handle persistent token storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize token storage."""
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, str] = {}

    async def async_load(self) -> None:
        """Load tokens from storage."""
        data = await self._store.async_load()
        self._data = data if data else {}

    async def async_get_token(self, property_id: str) -> str | None:
        """Get cached token for a property."""
        return self._data.get(property_id)

    async def async_save_token(self, property_id: str, token: str) -> None:
        """Save token for a property."""
        self._data[property_id] = token
        await self._store.async_save(self._data)

    async def async_clear_token(self, property_id: str) -> None:
        """Clear token for a property."""
        self._data.pop(property_id, None)
        await self._store.async_save(self._data)


class BIRDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching BIR data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        property_id: str,
        address: str,
        token_storage: BIRTokenStorage | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.session = session
        self.property_id = property_id
        self.address = address
        self._token: str | None = None
        self._token_storage = token_storage

    async def async_initialize(self) -> None:
        """Initialize coordinator and load cached token."""
        if self._token_storage:
            self._token = await self._token_storage.async_get_token(self.property_id)
            if self._token:
                _LOGGER.debug("Loaded cached token for property %s", self.property_id)

    async def async_test_connection(self) -> bool:
        """Test if we can connect to the BIR API.

        Returns:
            True if connection is successful.

        Raises:
            Exception: If connection fails.

        """
        # Just try to login to test the connection
        await self._login()
        return True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from BIR API."""
        try:
            # Ensure we have a valid token
            if not self._token:
                self._token = await self._login()

            # Try to fetch data
            try:
                return await self._fetch_pickup_dates()
            except ClientResponseError as err:
                if err.status == 401:
                    # Token expired, clear and refresh
                    _LOGGER.debug("Token expired, refreshing...")
                    await self._clear_token()
                    self._token = await self._login(force_refresh=True)
                    return await self._fetch_pickup_dates()
                raise

        except ClientResponseError as err:
            raise UpdateFailed(f"Error communicating with BIR API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _login(self, force_refresh: bool = False) -> str:
        """Login to BIR API and get token."""
        if self._token and not force_refresh:
            return self._token

        _LOGGER.debug("Logging in to BIR API")

        payload = {
            "applikasjonsId": API_APP_ID,
            "oppdragsgiverId": API_PROVIDER_ID,
        }

        timeout = ClientTimeout(total=API_TIMEOUT)
        async with self.session.post(
            API_LOGIN_URL, json=payload, timeout=timeout
        ) as response:
            response.raise_for_status()
            token = response.headers.get("Token")
            if not token:
                raise UpdateFailed("Login failed: Token not found in response headers")

            # Cache token in memory and persistent storage
            self._token = token
            if self._token_storage:
                await self._token_storage.async_save_token(self.property_id, token)
                _LOGGER.debug("Saved token to persistent storage")

            return token

    async def _clear_token(self) -> None:
        """Clear the cached token."""
        self._token = None
        if self._token_storage:
            await self._token_storage.async_clear_token(self.property_id)

    async def _fetch_pickup_dates(self) -> dict[str, Any]:
        """Fetch pickup dates from BIR API."""
        now = datetime.now()
        params = {
            "eiendomId": self.property_id,
            "datoFra": now.strftime("%Y-%m-%d"),
            "datoTil": (now + timedelta(days=PICKUP_LOOKUP_DAYS)).strftime("%Y-%m-%d"),
        }
        headers = {"Token": self._token}

        timeout = ClientTimeout(total=API_TIMEOUT)
        async with self.session.get(
            API_PICKUP_URL, headers=headers, params=params, timeout=timeout
        ) as response:
            response.raise_for_status()
            pickup_data = await response.json()

        _LOGGER.debug("Received %d pickup entries from BIR API", len(pickup_data))

        return self._process_pickup_data(pickup_data, reference_date=now.date())

    def _process_pickup_data(
        self, pickup_data: list[dict], reference_date: dt.date | None = None
    ) -> dict[str, Any]:
        """Process raw pickup data into structured format.

        Args:
            pickup_data: Raw pickup data from the API.
            reference_date: The date to use for calculating days_until.
                           Defaults to today if not provided.

        Returns:
            Dictionary mapping waste types to their next pickup information.

        """
        today = (
            reference_date if reference_date is not None else datetime.today().date()
        )
        next_pickups: dict[str, Any] = {}

        for item in pickup_data:
            fraksjon = item.get("fraksjon")
            if fraksjon not in WASTE_TYPE_MAP:
                continue

            english_name = WASTE_TYPE_MAP[fraksjon]
            pickup_date = datetime.strptime(item["dato"], "%Y-%m-%dT%H:%M:%S").date()
            days_until = max(0, (pickup_date - today).days)

            # Only keep the earliest pickup date for each waste type
            if (
                english_name not in next_pickups
                or pickup_date
                < datetime.strptime(
                    next_pickups[english_name]["date"], "%Y-%m-%d"
                ).date()
            ):
                next_pickups[english_name] = {
                    "date": pickup_date.strftime("%Y-%m-%d"),
                    "date_raw": item["dato"],
                    "days_until": days_until,
                    "waste_type": english_name,
                }

        return next_pickups


def extract_property_id(url: str) -> str | None:
    """Extract property ID from BIR URL."""
    match = re.search(r"[?&]rId=([^&]+)", url)
    return match.group(1) if match else None


def extract_address(url: str) -> str | None:
    """Extract address from BIR URL."""
    match = re.search(r"[?&]name=([^&]+)", url)
    if match:
        return unquote(match.group(1))
    return None


async def async_search_addresses(
    session: ClientSession, query: str, token: str | None = None
) -> list[dict[str, Any]]:
    """Search for addresses using the BIR API.

    Args:
        session: aiohttp client session.
        query: Address search query (street name, partial address, etc.).
        token: Optional auth token. If not provided, will login first.

    Returns:
        List of matching properties with id, address, municipality, etc.

    """
    # Get token if not provided
    if not token:
        payload = {
            "applikasjonsId": API_APP_ID,
            "oppdragsgiverId": API_PROVIDER_ID,
        }
        timeout = ClientTimeout(total=API_TIMEOUT)
        async with session.post(
            API_LOGIN_URL, json=payload, timeout=timeout
        ) as response:
            response.raise_for_status()
            token = response.headers.get("Token")
            if not token:
                raise ValueError("Login failed: Token not found")

    # Search for addresses
    params = {"adresse": query}
    headers = {"Token": token}
    timeout = ClientTimeout(total=API_TIMEOUT)

    async with session.get(
        API_ADDRESS_SEARCH_URL, headers=headers, params=params, timeout=timeout
    ) as response:
        response.raise_for_status()
        return await response.json()
