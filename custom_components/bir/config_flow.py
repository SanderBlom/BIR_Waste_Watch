"""Config flow for BIR Waste Watch integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import voluptuous as vol

from .const import CONF_ADDRESS, CONF_PROPERTY_ID, DOMAIN
from .coordinator import BIRDataUpdateCoordinator, async_search_addresses

_LOGGER = logging.getLogger(__name__)

# Minimum characters before searching
MIN_SEARCH_LENGTH = 3


class BIRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BIR Waste Watch."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._addresses: list[dict[str, Any]] = []
        self._search_query: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - address search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            search_query = user_input.get("address_search", "").strip()

            if len(search_query) < MIN_SEARCH_LENGTH:
                errors["base"] = "search_too_short"
            else:
                try:
                    session = async_get_clientsession(self.hass)
                    self._addresses = await async_search_addresses(
                        session, search_query
                    )
                    self._search_query = search_query

                    if not self._addresses:
                        errors["base"] = "no_addresses_found"
                    else:
                        # Move to address selection step
                        return await self.async_step_select_address()

                except Exception:
                    _LOGGER.exception("Error searching for addresses")
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address_search", default=""): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                            autocomplete="street-address",
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"min_chars": str(MIN_SEARCH_LENGTH)},
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_id = user_input.get("selected_address")

            if selected_id == "__search_again__":
                # Go back to search
                return await self.async_step_user()

            if selected_id:
                # Find the selected address
                selected = next(
                    (a for a in self._addresses if a["id"] == selected_id), None
                )
                if selected:
                    # Validate the property works
                    try:
                        session = async_get_clientsession(self.hass)
                        coordinator = BIRDataUpdateCoordinator(
                            self.hass,
                            session,
                            selected["id"],
                            selected["adresse"],
                        )
                        await coordinator.async_test_connection()

                        # Set unique ID to prevent duplicates
                        await self.async_set_unique_id(f"bir_{selected['id']}")
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=selected["adresse"],
                            data={
                                CONF_PROPERTY_ID: selected["id"],
                                CONF_ADDRESS: selected["adresse"],
                            },
                        )
                    except AbortFlow:
                        raise
                    except Exception:
                        _LOGGER.exception("Error validating property")
                        errors["base"] = "cannot_connect"

        # Build address options
        options = [
            SelectOptionDict(
                value=addr["id"],
                label=addr["adresse"],
            )
            for addr in self._addresses
        ]

        # Add search again option at the end
        options.append(
            SelectOptionDict(
                value="__search_again__",
                label="🔍 Search again...",
            )
        )

        return self.async_show_form(
            step_id="select_address",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_address"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "count": str(len(self._addresses)),
                "query": self._search_query,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return BIROptionsFlowHandler()


class BIROptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for BIR Waste Watch."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._addresses: list[dict[str, Any]] = []
        self._search_query: str = ""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address search step - go directly to search."""
        errors: dict[str, str] = {}
        current_address = self.config_entry.data.get(CONF_ADDRESS, "")

        if user_input is not None:
            search_query = user_input.get("address_search", "").strip()

            if len(search_query) < MIN_SEARCH_LENGTH:
                errors["base"] = "search_too_short"
            else:
                try:
                    session = async_get_clientsession(self.hass)
                    self._addresses = await async_search_addresses(
                        session, search_query
                    )
                    self._search_query = search_query

                    if not self._addresses:
                        errors["base"] = "no_addresses_found"
                    else:
                        return await self.async_step_select_address()

                except Exception:
                    _LOGGER.exception("Error searching for addresses")
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("address_search", default=current_address): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                            autocomplete="street-address",
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "min_chars": str(MIN_SEARCH_LENGTH),
                "current_address": current_address,
            },
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_id = user_input.get("selected_address")

            if selected_id == "__search_again__":
                return await self.async_step_init()

            if selected_id:
                selected = next(
                    (a for a in self._addresses if a["id"] == selected_id), None
                )
                if selected:
                    try:
                        session = async_get_clientsession(self.hass)
                        coordinator = BIRDataUpdateCoordinator(
                            self.hass,
                            session,
                            selected["id"],
                            selected["adresse"],
                        )
                        await coordinator.async_test_connection()

                        # Update the config entry with new address
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            title=selected["adresse"],
                            data={
                                CONF_PROPERTY_ID: selected["id"],
                                CONF_ADDRESS: selected["adresse"],
                            },
                            unique_id=f"bir_{selected['id']}",
                        )

                        return self.async_create_entry(title="", data={})
                    except Exception:
                        _LOGGER.exception("Error validating property")
                        errors["base"] = "cannot_connect"

        options = [
            SelectOptionDict(
                value=addr["id"],
                label=addr["adresse"],
            )
            for addr in self._addresses
        ]

        options.append(
            SelectOptionDict(
                value="__search_again__",
                label="🔍 Search again...",
            )
        )

        return self.async_show_form(
            step_id="select_address",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_address"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "count": str(len(self._addresses)),
                "query": self._search_query,
            },
        )
