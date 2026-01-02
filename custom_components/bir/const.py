"""Constants for BIR Waste Watch integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "bir"
MANUFACTURER: Final = "BIR"

# API endpoints
API_BASE_URL: Final = "https://webservice.bir.no/api"
API_LOGIN_URL: Final = f"{API_BASE_URL}/login"
API_PICKUP_URL: Final = f"{API_BASE_URL}/tomminger"

# API credentials
API_APP_ID: Final = "94FA72AD-583D-4AA3-988F-491F694DFB7B"
API_PROVIDER_ID: Final = "100;300;400"

# Update interval
SCAN_INTERVAL: Final = timedelta(hours=1)

# API request timeout (seconds)
API_TIMEOUT: Final = 30

# Waste type mappings (Norwegian to English)
WASTE_TYPE_MAP: Final = {
    "Restavfall": "Mixed Waste",
    "Papir": "Paper And Plastic",
    "Matavfall": "Food Waste",
    "Glass og metallemballasje": "Glass And Metal Packaging",
}

# Sensor types
SENSOR_TYPE_DATE: Final = "date"
SENSOR_TYPE_DAYS: Final = "days"

# Attributes
ATTR_LAST_UPDATED: Final = "last_updated"
ATTR_WASTE_TYPE: Final = "waste_type"
ATTR_PICKUP_DATE: Final = "pickup_date"

# Config keys
CONF_URL: Final = "url"
CONF_PROPERTY_ID: Final = "property_id"
CONF_ADDRESS: Final = "address"
