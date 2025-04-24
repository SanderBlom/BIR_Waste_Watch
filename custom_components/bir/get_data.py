import aiohttp
from datetime import datetime, timedelta
import re
import logging

# Global variable to store the token
_cached_token = None
_LOGGER = logging.getLogger(__name__)

async def login(session: aiohttp.ClientSession, force_refresh=False):
    """Login and retrieve a token, with an option to force refresh."""
    _LOGGER.debug("Trying to get a new token")
    global _cached_token
    if _cached_token and not force_refresh:
        return _cached_token

    url = "https://webservice.bir.no/api/login"
    payload = {
        "applikasjonsId": "94FA72AD-583D-4AA3-988F-491F694DFB7B",
        "oppdragsgiverId": "100;300;400"
    }

    try:
        async with session.post(url, json=payload) as response:
            response.raise_for_status()  # Raise an error for bad responses
            token = response.headers.get("Token")
            if not token:
                raise Exception("Login failed: Token not found in response headers")
            _cached_token = token
            return token
    except aiohttp.ClientResponseError as e:
        _LOGGER.error(f"Login failed: {e}")
        raise
    except aiohttp.ClientError as e:
        _LOGGER.error(f"An error occurred during login: {e}")
        raise

async def get_pickup_dates(session: aiohttp.ClientSession, url: str, token: str, logger: logging.Logger):
    """Fetch the pickup dates using the provided token."""
    if token is None:
        logger.debug("Token is none. Check that login was successful.")
        token = await login(session)

    pattern = r'[?&]rId=([^&]+)'
    match = re.search(pattern, url)
    logger.debug("The URL is: %s", url)

    if match:
        eiendom_id = match.group(1)
    else:
        raise Exception("Failed to extract eiendomId from URL")

    base_url = "https://webservice.bir.no/api/tomminger"
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    end_date = (today + timedelta(days=31)).strftime('%Y-%m-%d')
    params = {
        "eiendomId": eiendom_id,
        "datoFra": today_str,
        "datoTil": end_date
    }
    headers = {
        "Token": token
    }

    try:
        async with session.get(base_url, headers=headers, params=params) as response:
            response.raise_for_status()
            pickup_data = await response.json()
    except aiohttp.ClientResponseError as e:
        if e.status == 401:  # Unauthorized, try logging in again
            logger.debug("Token expired. Logging in again.")
            global _cached_token
            _cached_token = None
            token = await login(session, force_refresh=True)
            headers["Token"] = token
            async with session.get(base_url, headers=headers, params=params) as response:
                response.raise_for_status()
                pickup_data = await response.json()
        else:
            raise Exception("Failed to fetch pickup dates") from e

    # Initialize next pickup tracking
    next_pickups = {
        "Restavfall": None,
        "Papir": None,
        "Matavfall": None,
        "Glass og metallemballasje": None
    }

    name_map = {
        "Restavfall": "Mixed Waste",
        "Papir": "Paper And Plastic",
        "Matavfall": "Food Waste",
        "Glass og metallemballasje": "Glass and Metal Packaging"
    }
    today = datetime.today().date()

    logger.debug("Response from BIR API: %s", pickup_data)

    for item in pickup_data:
        fraksjon = item["fraksjon"]
        if fraksjon in next_pickups:
            # Convert pickup_date to a date without time
            pickup_date = datetime.strptime(item["dato"], '%Y-%m-%dT%H:%M:%S').date()
            days_until = (pickup_date - today).days
            if days_until < 0:
                days_until = 0
            # Check if we have no date yet or if the current date is earlier
            if next_pickups[fraksjon] is None or pickup_date < datetime.strptime(next_pickups[fraksjon]["dato"], '%Y-%m-%dT%H:%M:%S').date():
                next_pickups[fraksjon] = {
                    "dato": item["dato"],
                    "type": name_map[fraksjon],
                    "days_until": days_until
                }

    # Return only pickups that are not None, with English names
    return {name_map[k]: v for k, v in next_pickups.items() if v is not None}

