"""Fixtures for BIR Waste Watch tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Domain of the integration
DOMAIN = "bir"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    return


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Address",
        data={
            "url": "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress"
        },
        unique_id="bir_12345",
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.bir.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_pickup_data() -> dict:
    """Return mock pickup data."""
    return {
        "Mixed Waste": {
            "date": "2024-01-15",
            "date_raw": "2024-01-15T00:00:00",
            "days_until": 5,
            "waste_type": "Mixed Waste",
        },
        "Paper And Plastic": {
            "date": "2024-01-20",
            "date_raw": "2024-01-20T00:00:00",
            "days_until": 10,
            "waste_type": "Paper And Plastic",
        },
        "Food Waste": {
            "date": "2024-01-12",
            "date_raw": "2024-01-12T00:00:00",
            "days_until": 2,
            "waste_type": "Food Waste",
        },
        "Glass And Metal Packaging": {
            "date": "2024-02-01",
            "date_raw": "2024-02-01T00:00:00",
            "days_until": 22,
            "waste_type": "Glass And Metal Packaging",
        },
    }


@pytest.fixture
def mock_coordinator(mock_pickup_data) -> Generator[AsyncMock]:
    """Mock the BIRDataUpdateCoordinator."""
    with patch(
        "custom_components.bir.coordinator.BIRDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = MagicMock()
        mock_coordinator.data = mock_pickup_data
        mock_coordinator.address = "Test Address"
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        yield mock_coordinator


@pytest.fixture
def mock_coordinator_login() -> Generator[AsyncMock]:
    """Mock the coordinator login."""
    with patch(
        "custom_components.bir.coordinator.BIRDataUpdateCoordinator._login",
        return_value="mock_token_12345",
    ) as mock:
        yield mock
