from datetime import datetime, timedelta
import aiohttp
from homeassistant.components.sensor import SensorEntity
import logging
from .get_data import get_dates
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from typing import Any, Dict, List, Optional

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

    hass.bus.async_listen_once("homeassistant_stop", close_session)

    data = await get_dates(session, url)

    if data:
        sensors: List[SensorEntity] = []
        for waste_type, date in data.items():
            collection_sensor = WasteCollectionSensorDates(session, url, waste_type, date, config_entry.entry_id)
            days_until_sensor = WasteCollectionSensorDays(session, url, waste_type, date, config_entry.entry_id)
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
        data = await get_dates(self._session, self._url)
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
        data = await get_dates(self._session, self._url)
        self._state = data.get(self._waste_type, NA_STRING) if data else NA_STRING

class WasteCollectionSensorDays(WasteCollectionSensorBase):
    """Sensor for showing days until the next waste collection."""

    def __init__(self, session: aiohttp.ClientSession, url: str, waste_type: str, date: str, entry_id: str) -> None:
        super().__init__(session, url, waste_type, entry_id)
        self._date = date

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
        return self._calculate_days_until_pickup()

    def _calculate_days_until_pickup(self) -> int:
        """Calculate the days until the next waste collection."""
        today = datetime.now().date()
        pickup_date_obj = datetime.strptime(self._date, "%Y-%m-%d").date()
        return (pickup_date_obj - today).days
