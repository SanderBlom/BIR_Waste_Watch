"""Test BIR Waste Watch integration init."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bir import (
    async_migrate_entry,
    async_setup_entry,
    async_update_listener,
)

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


@pytest.mark.parametrize(
    ("addresses", "expected_id", "expected_address"),
    [
        ([{"id": "67890", "adresse": "New address"}], "67890", "New address"),
        ([], "12345", "Old Address"),
        (ConnectionError("API unavailable"), "12345", "Old Address"),
    ],
)
async def test_migrate_legacy_entry(
    hass: HomeAssistant,
    addresses: list[dict] | Exception,
    expected_id: str,
    expected_address: str,
) -> None:
    """Migrate URL entries, falling back to the old ID if lookup fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "url": "https://bir.no/tjenester/tommekalender/"
            "?rId=12345&name=Old%20Address"
        },
        version=1,
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.bir.async_search_addresses",
        new_callable=AsyncMock,
        side_effect=addresses if isinstance(addresses, Exception) else None,
        return_value=addresses if isinstance(addresses, list) else None,
    ):
        assert await async_migrate_entry(hass, entry)

    assert entry.version == 2
    assert entry.data == {"property_id": expected_id, "address": expected_address}
    assert entry.title == expected_address


async def test_migrate_entry_with_property_id(hass: HomeAssistant) -> None:
    """An existing property ID only needs a version bump."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"property_id": "12345", "address": "Old Address"},
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert entry.data["property_id"] == "12345"


async def test_update_listener_renames_device_and_reloads(
    hass: HomeAssistant,
) -> None:
    """Changing an address updates the device name and reloads its entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"property_id": "12345", "address": "New address"},
        version=2,
    )
    entry.add_to_hass(hass)
    device = MagicMock(id="device-id")
    registry = MagicMock()
    registry.async_get_device.return_value = device

    with (
        patch("custom_components.bir.dr.async_get", return_value=registry),
        patch.object(
            hass.config_entries, "async_reload", new_callable=AsyncMock
        ) as reload,
    ):
        await async_update_listener(hass, entry)

    registry.async_get_device.assert_called_once_with(identifiers={(DOMAIN, "12345")})
    registry.async_update_device.assert_called_once_with(
        "device-id", name="New address"
    )
    reload.assert_awaited_once_with(entry.entry_id)


async def test_setup_rejects_legacy_url_without_property_id(
    hass: HomeAssistant,
) -> None:
    """Do not set up a URL-based entry that has no property ID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"url": "https://bir.no/tjenester/tommekalender/?name=OldAddress"},
        version=2,
    )
    entry.add_to_hass(hass)

    assert not await async_setup_entry(hass, entry)
    assert DOMAIN not in hass.data
