import logging
from datetime import timedelta, datetime
import aiohttp
from bs4 import BeautifulSoup
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

async def get_dates(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            return "Failed to get content"

        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        data = {}

        target_items = soup.select('.address-page-box__list__item')

        for item in target_items:
            text_content_elem = item.select_one('.text-content__inner')
            date_month_elem = item.select_one('.date__month')

            if text_content_elem and date_month_elem:
                text_content = text_content_elem.get_text(strip=True)
                date_month = date_month_elem.get_text(strip=True)

                date_parts = date_month.split(". ")
                if len(date_parts) < 2:
                    continue

                date_day = date_parts[0].strip()
                date_month = date_parts[1].strip()

                date, err = parseToDate(date_day, date_month)
                if err:
                    continue

                formatted_date = date.strftime("%Y-%m-%d")

                if "Restavfall" in text_content:
                    data['mixed_waste'] = formatted_date
                elif "Papir og plastemballasje" in text_content:
                    data['paper_and_plastic_waste'] = formatted_date
                elif "Matavfall" in text_content:
                    data['food_waste'] = formatted_date

        return data

def parseToDate(date_day, date_month):
    try:
        date_str = f"{date_day} {date_month} 2023"
        return datetime.strptime(date_str, '%d %b %Y'), None
    except Exception as e:
        return None, str(e)

async def async_setup_entry(hass, config_entry, async_add_entities):
    url = config_entry.data.get("url")
    update_interval = config_entry.data.get("update_interval", 4)  # Default to 4 if not found
    session = aiohttp.ClientSession()

    data = await get_dates(session, url)
    
    if data:
        sensors = []
        for waste_type, date in data.items():
            sensor = WasteCollectionSensor(session, url, waste_type, date, config_entry.entry_id)
            sensors.append(sensor)
            
            # Set up the update interval for each sensor
            async_track_time_interval(hass, sensor.async_update, timedelta(hours=int(update_interval)))

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
