from datetime import datetime, timedelta
import aiohttp
from homeassistant.components.sensor import SensorEntity
import logging
from .get_data import get_dates

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)
NA_STRING = "N/A"

async def async_setup_entry(hass, config_entry, async_add_entities):
    url = config_entry.data.get("url")
    session = aiohttp.ClientSession()

    async def close_session(event):
        await session.close()

    hass.bus.async_listen_once("homeassistant_stop", close_session)

    data = await get_dates(session, url)

    if data:
        sensors = []
        for waste_type, date in data.items():
            collection_sensor = WasteCollectionSensorDates(
                session, url, waste_type, date, config_entry.entry_id
            )
            days_until_sensor = WasteCollectionSensorDays(
                session, url, waste_type, date, config_entry.entry_id
            )
            sensors.extend([collection_sensor, days_until_sensor])

            # Update the sensors on the first run
            await collection_sensor.async_update()
            await days_until_sensor.async_update()

        if sensors:
            async_add_entities(sensors, True)

class WasteCollectionSensorBase(SensorEntity):
    def __init__(self, session, url, waste_type, entry_id):
        self._session = session
        self._url = url
        self._waste_type = waste_type
        self._entry_id = entry_id
        self._last_updated = None

    @property
    def unique_id(self):
        raise NotImplementedError

    @property
    def icon(self):
        return "mdi:trash-can"

    @property
    def extra_state_attributes(self):
        return {"Last updated": self._last_updated}

    async def async_update(self, *_):
        data = await get_dates(self._session, self._url)
        if data:
            self._last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class WasteCollectionSensorDates(WasteCollectionSensorBase):
    def __init__(self, session, url, waste_type, date, entry_id):
        super().__init__(session, url, waste_type, entry_id)
        self._date = date
        self._state = NA_STRING

    @property
    def unique_id(self):
        return f"{self._entry_id}_{self._waste_type}_date"

    @property
    def name(self):
        return f"{self._waste_type.replace('_', ' ').title()} Collection Date"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        data = await get_dates(self._session, self._url)
        self._state = data.get(self._waste_type, NA_STRING) if data else NA_STRING

class WasteCollectionSensorDays(WasteCollectionSensorBase):
    def __init__(self, session, url, waste_type, date, entry_id):
        super().__init__(session, url, waste_type, entry_id)
        self._date = date

    @property
    def unique_id(self):
        return f"{self._entry_id}_{self._waste_type}_days"

    @property
    def name(self):
        return f"{self._waste_type.replace('_', ' ').title()} Days Until Pickup"

    @property
    def state(self):
        return self._calculate_days_until_pickup()

    def _calculate_days_until_pickup(self):
        today = datetime.now().date()
        pickup_date_obj = datetime.strptime(self._date, "%Y-%m-%d").date()
        return (pickup_date_obj - today).days
