"""Test BIR Waste Watch sensor platform."""

from unittest.mock import AsyncMock, MagicMock, patch

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "bir"


def _create_mock_coordinator(mock_pickup_data: dict) -> MagicMock:
    """Create a mock coordinator with all required async methods."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = mock_pickup_data
    mock_coordinator.address = "Test Address"
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    mock_coordinator.async_initialize = AsyncMock()
    return mock_coordinator


def _create_mock_token_storage() -> MagicMock:
    """Create a mock token storage with all required async methods."""
    mock_token_storage = MagicMock()
    mock_token_storage.async_load = AsyncMock()
    return mock_token_storage


@freeze_time("2024-01-10")
async def test_sensor_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pickup_data: dict,
) -> None:
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)

    mock_coordinator = _create_mock_coordinator(mock_pickup_data)
    mock_token_storage = _create_mock_token_storage()

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

    # Check that date sensors were created
    assert (
        hass.states.get("sensor.bir_test_address_mixed_waste_collection_date")
        is not None
    )
    assert (
        hass.states.get("sensor.bir_test_address_paper_and_plastic_collection_date")
        is not None
    )
    assert (
        hass.states.get("sensor.bir_test_address_food_waste_collection_date")
        is not None
    )
    assert (
        hass.states.get(
            "sensor.bir_test_address_glass_and_metal_packaging_collection_date"
        )
        is not None
    )

    # Check that days until sensors were created
    assert (
        hass.states.get("sensor.bir_test_address_mixed_waste_days_until_pickup")
        is not None
    )
    assert (
        hass.states.get("sensor.bir_test_address_paper_and_plastic_days_until_pickup")
        is not None
    )
    assert (
        hass.states.get("sensor.bir_test_address_food_waste_days_until_pickup")
        is not None
    )
    assert (
        hass.states.get(
            "sensor.bir_test_address_glass_and_metal_packaging_days_until_pickup"
        )
        is not None
    )


@freeze_time("2024-01-10")
async def test_sensor_states(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pickup_data: dict,
) -> None:
    """Test sensor states are correct."""
    mock_config_entry.add_to_hass(hass)

    mock_coordinator = _create_mock_coordinator(mock_pickup_data)
    mock_token_storage = _create_mock_token_storage()

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

    # Check date sensor states
    mixed_waste_date = hass.states.get(
        "sensor.bir_test_address_mixed_waste_collection_date"
    )
    assert mixed_waste_date.state == "2024-01-15"

    food_waste_date = hass.states.get(
        "sensor.bir_test_address_food_waste_collection_date"
    )
    assert food_waste_date.state == "2024-01-12"

    # Check days until sensor states
    mixed_waste_days = hass.states.get(
        "sensor.bir_test_address_mixed_waste_days_until_pickup"
    )
    assert mixed_waste_days.state == "5"

    food_waste_days = hass.states.get(
        "sensor.bir_test_address_food_waste_days_until_pickup"
    )
    assert food_waste_days.state == "2"


async def test_sensor_no_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test sensor handles no data gracefully."""
    mock_config_entry.add_to_hass(hass)

    mock_coordinator = MagicMock()
    mock_coordinator.data = {}  # Empty data
    mock_coordinator.address = "Test Address"
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    mock_coordinator.async_initialize = AsyncMock()

    mock_token_storage = _create_mock_token_storage()

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

    # No sensors should be created when there's no data
    assert (
        hass.states.get("sensor.bir_test_address_mixed_waste_collection_date") is None
    )
