"""BIR Waste Watch integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_URL, DOMAIN
from .coordinator import (
    BIRDataUpdateCoordinator,
    BIRTokenStorage,
    extract_address,
    extract_property_id,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the BIR Waste Watch integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BIR Waste Watch from a config entry."""
    url = entry.data[CONF_URL]
    property_id = extract_property_id(url)
    address = extract_address(url) or "Unknown"

    if not property_id:
        _LOGGER.error("Could not extract property ID from URL")
        return False

    session = async_get_clientsession(hass)

    # Create token storage for persistent token caching
    token_storage = BIRTokenStorage(hass)
    await token_storage.async_load()

    coordinator = BIRDataUpdateCoordinator(
        hass,
        session,
        property_id,
        address,
        token_storage=token_storage,
    )

    # Initialize coordinator (loads cached token)
    await coordinator.async_initialize()

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BIR Waste Watch config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
