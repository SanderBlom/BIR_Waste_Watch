import logging
from datetime import datetime
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

MONTH_MAP = {
    "jan": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    "apr": "Apr",
    "mai": "May",
    "jun": "Jun",
    "jul": "Jul",
    "aug": "Aug",
    "sep": "Sep",
    "okt": "Oct",
    "nov": "Nov",
    "des": "Dec",
}

async def get_dates(session, url):
    _LOGGER.debug(f"Attempting to fetch data from URL: {url}")
    
    async with session.get(url) as response:
        if response.status != 200:
            _LOGGER.error(f"Failed to get content from URL: {url}. HTTP Status Code: {response.status}")
            return "Failed to get content"

        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        data = {}
        target_items = soup.select('.address-page-box__list__item')
        
        _LOGGER.debug(f"Found {len(target_items)} target items.")

        for item in target_items:
            text_content_elem = item.select_one('.text-content__inner')
            date_month_elem = item.select_one('.date__month')

            if text_content_elem and date_month_elem:
                text_content = text_content_elem.get_text(strip=True)
                date_month = date_month_elem.get_text(strip=True)

                date_parts = date_month.split(". ")
                if len(date_parts) < 2:
                    _LOGGER.warning("Could not split date into day and month")
                    continue

                date_day = date_parts[0].strip()
                date_month = date_parts[1].strip()
                
                # Translate month to English abbreviation
                date_month = MONTH_MAP.get(date_month.lower(), date_month)

                date, err = parseToDate(date_day, date_month)
                if err:
                    _LOGGER.error(f"Failed to parse date. Error: {err}")
                    continue

                formatted_date = date.strftime("%Y-%m-%d")

                if "Restavfall" in text_content:
                    data['mixed_waste'] = formatted_date
                elif "Papir og plastemballasje" in text_content:
                    data['paper_and_plastic_waste'] = formatted_date
                elif "Matavfall" in text_content:
                    data['food_waste'] = formatted_date

        _LOGGER.debug(f"Collected data: {data}")

        return data

def parseToDate(date_day, date_month):
    try:
        # Get the current year
        current_year = datetime.now().year

        # If the current month is December and the pickup month is January,
        # increment the year by 1
        if datetime.now().month == 12 and date_month.lower() == 'jan':
            current_year += 1

        date_str = f"{date_day} {date_month} {current_year}"
        return datetime.strptime(date_str, '%d %b %Y'), None
    except Exception as e:
        _LOGGER.error(f"Exception while parsing date: {str(e)}")
        return None, str(e)
