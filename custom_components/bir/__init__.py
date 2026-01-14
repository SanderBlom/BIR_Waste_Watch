"""BIR Waste Watch integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ADDRESS, CONF_PROPERTY_ID, CONF_URL, DOMAIN
from .coordinator import (
    BIRDataUpdateCoordinator,
    BIRTokenStorage,
    async_search_addresses,
    extract_address,
    extract_property_id,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to new format.

    Version 1 -> 2: Migrate from URL-based config to property_id based config.
    The old rId from the URL may not work with the current API, so we try to
    look up the property by address.
    """
    _LOGGER.debug("Migrating BIR config entry from version %s", entry.version)

    if entry.version == 1:
        # Check if this is an old URL-based entry that needs migration
        if CONF_URL in entry.data and CONF_PROPERTY_ID not in entry.data:
            url = entry.data[CONF_URL]
            old_property_id = extract_property_id(url)
            address = extract_address(url) or "Unknown"

            _LOGGER.info(
                "Migrating BIR entry from URL format. Address: %s, Old ID: %s",
                address,
                old_property_id,
            )

            # Try to look up the property by address to get new ID
            new_property_id = old_property_id
            try:
                session = async_get_clientsession(hass)
                # Search for the address
                addresses = await async_search_addresses(session, address)
                if addresses:
                    # Use the first match
                    new_property_id = addresses[0]["id"]
                    address = addresses[0].get("adresse", address)
                    _LOGGER.info(
                        "Found new property ID via address search: %s -> %s",
                        old_property_id,
                        new_property_id,
                    )
            except Exception:
                _LOGGER.warning(
                    "Could not look up new property ID for %s, using old ID",
                    address,
                )

            # Update to new format
            new_data = {
                CONF_PROPERTY_ID: new_property_id,
                CONF_ADDRESS: address,
            }

            hass.config_entries.async_update_entry(
                entry, data=new_data, version=2, title=address
            )
            _LOGGER.info("Migration to version 2 successful for %s", address)

        else:
            # Already has property_id, just bump version
            hass.config_entries.async_update_entry(entry, version=2)

    return True

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the BIR Waste Watch integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BIR Waste Watch from a config entry."""
    # Support both new (property_id) and legacy (url) config formats
    if CONF_PROPERTY_ID in entry.data:
        # New format: direct property_id and address
        property_id = entry.data[CONF_PROPERTY_ID]
        address = entry.data.get(CONF_ADDRESS, "Unknown")
    else:
        # Legacy format: extract from URL
        url = entry.data[CONF_URL]
        property_id = extract_property_id(url)
        address = extract_address(url) or "Unknown"

        if not property_id:
            _LOGGER.error("Could not extract property ID from URL")
            return False

    session = async_get_clientsession(hass)

    # Create token storage for persistent token caching
    token_storage = BIRTokenStorage(hass)
    await token_storage.async_load()

    coordinator = BIRDataUpdateCoordinator(
        hass,
        session,
        property_id,
        address,
        token_storage=token_storage,
    )

    # Initialize coordinator (loads cached token)
    await coordinator.async_initialize()

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener to handle options/config changes
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry updates (e.g., address change via options flow)."""
    # Get the new address from the updated config
    new_address = entry.data.get(CONF_ADDRESS, "Unknown")
    property_id = entry.data.get(CONF_PROPERTY_ID)

    # Update the device registry with the new name
    if property_id:
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(identifiers={(DOMAIN, property_id)})
        if device:
            device_registry.async_update_device(device.id, name=new_address)
            _LOGGER.debug("Updated device name to: %s", new_address)

    # Reload the entry to refresh coordinator with new data
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BIR Waste Watch config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
