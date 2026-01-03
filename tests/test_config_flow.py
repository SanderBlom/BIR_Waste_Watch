"""Test BIR Waste Watch config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bir.config_flow import BIRConfigFlow
from custom_components.bir.const import DOMAIN

# Sample address search results from BIR API
MOCK_ADDRESSES = [
    {"id": "12345", "adresse": "Testveien 1", "kommune": "Bergen"},
    {"id": "12346", "adresse": "Testveien 2", "kommune": "Bergen"},
    {"id": "12347", "adresse": "Testveien 3", "kommune": "Bergen"},
]


@pytest.fixture(autouse=True)
def register_config_flow(hass: HomeAssistant) -> None:
    """Register the config flow handler."""
    config_entries.HANDLERS.register(DOMAIN)(BIRConfigFlow)


async def test_form_shows_search(hass: HomeAssistant) -> None:
    """Test we get the address search form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_search_too_short(hass: HomeAssistant) -> None:
    """Test error when search query is too short."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"address_search": "ab"},
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "search_too_short"}


async def test_search_no_results(hass: HomeAssistant) -> None:
    """Test error when no addresses are found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Nonexistent street"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "no_addresses_found"}


async def test_search_connection_error(hass: HomeAssistant) -> None:
    """Test error when API connection fails during search."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        side_effect=Exception("Connection failed"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_search_shows_select_step(hass: HomeAssistant) -> None:
    """Test successful search shows address selection step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=MOCK_ADDRESSES,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "select_address"


async def test_select_address_creates_entry(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """Test selecting an address creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Step 1: Search for addresses
    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=MOCK_ADDRESSES,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "select_address"

    # Step 2: Select an address
    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"selected_address": "12345"},
        )
        await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Testveien 1"
    assert result3["data"] == {
        "property_id": "12345",
        "address": "Testveien 1",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_select_address_validation_error(hass: HomeAssistant) -> None:
    """Test error when address validation fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Step 1: Search for addresses
    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=MOCK_ADDRESSES,
    ):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    # Step 2: Select an address (fails validation)
    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
        side_effect=Exception("Validation failed"),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"selected_address": "12345"},
        )

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "select_address"
    assert result3["errors"] == {"base": "cannot_connect"}


async def test_search_again_option(hass: HomeAssistant) -> None:
    """Test selecting 'search again' returns to search step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Step 1: Search for addresses
    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=MOCK_ADDRESSES,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    assert result2["step_id"] == "select_address"

    # Step 2: Select "search again"
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_address": "__search_again__"},
    )

    assert result3["type"] == FlowResultType.FORM
    assert result3["step_id"] == "user"


async def test_already_configured(hass: HomeAssistant) -> None:
    """Test we abort if address is already configured."""
    # Create an existing entry with the same unique_id
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Testveien 1",
        data={"property_id": "12345", "address": "Testveien 1"},
        unique_id="bir_12345",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Step 1: Search for addresses
    with patch(
        "custom_components.bir.config_flow.async_search_addresses",
        new_callable=AsyncMock,
        return_value=MOCK_ADDRESSES,
    ):
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"address_search": "Testveien"},
        )

    # Step 2: Select the already configured address
    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"selected_address": "12345"},
        )

    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "already_configured"
