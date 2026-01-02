"""Test BIR Waste Watch integration init."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "bir"


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pickup_data: dict,
) -> None:
    """Test successful setup of config entry."""
    mock_config_entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.data = mock_pickup_data
    mock_coordinator.address = "Test Address"
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    mock_coordinator.async_initialize = AsyncMock()

    mock_token_storage = MagicMock()
    mock_token_storage.async_load = AsyncMock()

    with (
        patch(
            "custom_components.bir.BIRDataUpdateCoordinator",
            return_value=mock_coordinator,
        ),
        patch(
            "custom_components.bir.BIRTokenStorage",
            return_value=mock_token_storage,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pickup_data: dict,
) -> None:
    """Test successful unload of config entry."""
    mock_config_entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.data = mock_pickup_data
    mock_coordinator.address = "Test Address"
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    mock_coordinator.async_initialize = AsyncMock()

    mock_token_storage = MagicMock()
    mock_token_storage.async_load = AsyncMock()

    with (
        patch(
            "custom_components.bir.BIRDataUpdateCoordinator",
            return_value=mock_coordinator,
        ),
        patch(
            "custom_components.bir.BIRTokenStorage",
            return_value=mock_token_storage,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state == ConfigEntryState.LOADED

        await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]
