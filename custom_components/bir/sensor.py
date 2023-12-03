from datetime import timedelta, datetime
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
import logging
from .get_data import get_dates 
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    url = config_entry.data.get("url")
    session = aiohttp.ClientSession()

    # Register a callback to close the session on Home Assistant's shutdown
    async def close_session(event):
        await session.close()

    hass.bus.async_listen_once("homeassistant_stop", close_session)

    data = await get_dates(session, url)

    if data:
        sensors = []
        for waste_type, date in data.items():
            sensor = WasteCollectionSensor(session, url, waste_type, date, config_entry.entry_id)
            sensors.append(sensor)

            # Update the sensor on the first run
            await sensor.async_update()

        if sensors:
            async_add_entities(sensors, True)                


class WasteCollectionSensor(SensorEntity):
    SCAN_INTERVAL = timedelta(hours=4)
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
            'Last updated': self._last_updated
        }

    async def async_update(self, *_):
        data = await get_dates(self._session, self._url)
        if data:
            self._state = data.get(self._waste_type, "N/A")
            self._last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
