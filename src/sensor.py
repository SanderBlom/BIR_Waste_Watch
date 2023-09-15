from datetime import timedelta, datetime
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
import logging
from .get_data import get_dates 
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    url = config_entry.data.get("url")
    update_interval = config_entry.data.get("update_interval", 4)
    session = aiohttp.ClientSession()

    data = await get_dates(session, url)
    
    _LOGGER.debug(f"Data retrieved from get_dates function: {data}")  # Debug log to check data

    if data:
        sensors = []
        for waste_type, date in data.items():
            sensor = WasteCollectionSensor(session, url, waste_type, date, config_entry.entry_id)
            sensors.append(sensor)
            
            async_track_time_interval(hass, sensor.async_update, timedelta(hours=int(update_interval)))
        
        _LOGGER.debug(f"Sensors to add: {sensors}")  # Debug log to check sensors

        if sensors:
            async_add_entities(sensors, True)


class WasteCollectionSensor(SensorEntity):
    def __init__(self, session, url, waste_type, state, entry_id):
        self._session = session
        self._url = url
        self._waste_type = waste_type
        self._state = state
        self._entry_id = entry_id
        self._last_updated = None  # Initialize last updated attribute

    @property
    def entity_registry_enabled_default(self) -> bool:
        return True

    @property
    def unique_id(self):
        return f"{self._entry_id}_{self._waste_type}"

    @property
    def name(self):
        return f"{self._waste_type.replace('_', ' ').title()}"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            'Last': self._last_updated
        }

    async def async_update(self, *_):
        data = await get_dates(self._session, self._url)
        if data:
            self._state = data.get(self._waste_type, "N/A")
            self._last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
