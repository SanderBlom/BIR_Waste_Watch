from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

CONFIG_SCHEMA = cv.config_entry_only_config_schema("bir")

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the BIR Waste Watch integration."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up BIR Waste Watch from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload BIR Waste Watch config entry."""
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return True
