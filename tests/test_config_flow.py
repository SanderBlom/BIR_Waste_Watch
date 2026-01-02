"""Test BIR Waste Watch config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

DOMAIN = "bir"


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_valid_url(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test we can configure with a valid URL."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "TestAddress"
    assert result2["data"] == {
        "url": "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress"
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_domain(hass: HomeAssistant) -> None:
    """Test we handle invalid domain."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Note: config_flow validates domain before checking parameters,
    # so we need a URL with valid params but wrong domain
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "https://example.com/page?rId=123&name=Test",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_url_domain"}


async def test_form_missing_parameters(hass: HomeAssistant) -> None:
    """Test we handle missing URL parameters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "https://bir.no/tjenester/tommekalender/",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "missing_parameters"}


async def test_form_missing_rid(hass: HomeAssistant) -> None:
    """Test we handle missing rId parameter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "https://bir.no/tjenester/tommekalender/?name=TestAddress",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "missing_parameters"}


async def test_form_missing_name(hass: HomeAssistant) -> None:
    """Test we handle missing name parameter."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "https://bir.no/tjenester/tommekalender/?rId=12345",
        },
    )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "missing_parameters"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle connection errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
        side_effect=Exception("Connection failed"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_already_configured(hass: HomeAssistant, mock_config_entry) -> None:
    """Test we handle already configured entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.bir.config_flow.BIRDataUpdateCoordinator.async_test_connection",
        new_callable=AsyncMock,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress",
            },
        )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
