from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
import logging
from .get_data import get_pickup_dates, login
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from typing import Any, Dict, List, Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)
NA_STRING = "N/A"

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Any) -> None:
    """Set up the sensor platform.

    Args:
        hass: HomeAssistant instance.
        config_entry: Configuration entry for this sensor.
        async_add_entities: Function to add entities to the platform.
    """
    url = config_entry.data.get("url")
    session = aiohttp.ClientSession()

    async def close_session(event: Any) -> None:
        """Close the aiohttp session on Home Assistant stop event."""
        await session.close()

    # Register for Home Assistant stop event to close the session
    hass.bus.async_listen_once("homeassistant_stop", close_session)

    token = await login(session, _LOGGER)

    data = await get_pickup_dates(session, url, token, _LOGGER)

    if data:
        sensors: List[SensorEntity] = []
        for waste_type, waste_info in data.items():
            collection_sensor = WasteCollectionSensorDates(session, url, waste_type, waste_info['dato'], config_entry.entry_id)
            days_until_sensor = WasteCollectionSensorDays(session, url, waste_type, waste_info['days_until'], config_entry.entry_id)
            sensors.extend([collection_sensor, days_until_sensor])

            await collection_sensor.async_update()
            await days_until_sensor.async_update()

        if sensors:
            async_add_entities(sensors, True)

class WasteCollectionSensorBase(SensorEntity):
    """Base sensor for waste collection."""

    def __init__(self, session: aiohttp.ClientSession, url: str, waste_type: str, entry_id: str) -> None:
        self._session = session
        self._url = url
        self._waste_type = waste_type
        self._entry_id = entry_id
        self._last_updated: Optional[str] = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        raise NotImplementedError

    @property
    def icon(self) -> str:
        """Return the icon to be used for this sensor."""
        return "mdi:trash-can"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {"Last updated": self._last_updated}

    async def async_update(self) -> None:
        """Update the sensor state."""
        token = await login(self._session, _LOGGER)  # Use cached token
        data = await get_pickup_dates(self._session, self._url, token, _LOGGER)
        if data:
            self._last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class WasteCollectionSensorDates(WasteCollectionSensorBase):
    """Sensor for showing waste collection dates."""

    def __init__(self, session: aiohttp.ClientSession, url: str, waste_type: str, date: str, entry_id: str) -> None:
        super().__init__(session, url, waste_type, entry_id)
        self._date = date
        self._state = NA_STRING

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._entry_id}_{self._waste_type}_date"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._waste_type.replace('_', ' ').title()} Collection Date"

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    async def async_update(self) -> None:
        """Update the sensor state (pickup date)."""
        token = await login(self._session, _LOGGER)  # Use cached token
        data = await get_pickup_dates(self._session, self._url, token, _LOGGER)
        if data and self._waste_type in data:
            self._state = data[self._waste_type]['dato']
        else:
            self._state = NA_STRING

class WasteCollectionSensorDays(WasteCollectionSensorBase):
    """Sensor for showing days until the next waste collection."""

    def __init__(self, session: aiohttp.ClientSession, url: str, waste_type: str, days_until: int, entry_id: str) -> None:
        super().__init__(session, url, waste_type, entry_id)
        self._days_until = days_until

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self._entry_id}_{self._waste_type}_days"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._waste_type.replace('_', ' ').title()} Days Until Pickup"

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._days_until

    async def async_update(self) -> None:
        """Update the sensor state (days until pickup)."""
        token = await login(self._session, _LOGGER)  # Use cached token
        data = await get_pickup_dates(self._session, self._url, token, _LOGGER)
        if data and self._waste_type in data:
            self._days_until = data[self._waste_type]['days_until']
