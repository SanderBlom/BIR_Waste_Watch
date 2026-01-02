"""Config flow for BIR Waste Watch integration."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import parse_qs, urlparse

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .const import CONF_URL, DOMAIN
from .coordinator import BIRDataUpdateCoordinator, extract_address, extract_property_id

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=""): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    url = data[CONF_URL]
    property_id = extract_property_id(url)
    address = extract_address(url)

    if not property_id:
        raise InvalidPropertyId

    session = async_get_clientsession(hass)
    coordinator = BIRDataUpdateCoordinator(
        hass,
        session,
        property_id,
        address or "Unknown",
    )

    # Test the connection
    await coordinator.async_test_connection()

    return {
        "title": address or f"Property {property_id}",
        "property_id": property_id,
    }


class BIRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BIR Waste Watch."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input.get(CONF_URL, "")
            parsed_url = urlparse(url)

            # Check if the URL is from bir.no
            if parsed_url.netloc != "bir.no":
                errors["base"] = "invalid_url_domain"
            else:
                # Check if the URL contains rId and name parameters
                query_params = parse_qs(parsed_url.query)
                if "rId" not in query_params or "name" not in query_params:
                    errors["base"] = "missing_parameters"

            if not errors:
                try:
                    info = await validate_input(self.hass, user_input)
                except InvalidPropertyId:
                    errors["base"] = "missing_parameters"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "cannot_connect"
                else:
                    # Set unique ID to prevent duplicate entries
                    property_id = extract_property_id(url)
                    await self.async_set_unique_id(f"bir_{property_id}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=info["title"],
                        data={CONF_URL: url},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class InvalidPropertyId(Exception):
    """Error to indicate invalid property ID."""
