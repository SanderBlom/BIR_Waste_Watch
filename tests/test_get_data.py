"""Test BIR Waste Watch coordinator module."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.bir.coordinator import (
    BIRDataUpdateCoordinator,
    extract_address,
    extract_property_id,
)


class TestExtractFunctions:
    """Tests for URL extraction functions."""

    def test_extract_property_id_valid(self):
        """Test extracting property ID from valid URL."""
        url = "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress"
        assert extract_property_id(url) == "12345"

    def test_extract_property_id_missing(self):
        """Test extracting property ID from URL without rId."""
        url = "https://bir.no/tjenester/tommekalender/?name=TestAddress"
        assert extract_property_id(url) is None

    def test_extract_address_valid(self):
        """Test extracting address from valid URL."""
        url = "https://bir.no/tjenester/tommekalender/?rId=12345&name=TestAddress"
        assert extract_address(url) == "TestAddress"

    def test_extract_address_encoded(self):
        """Test extracting URL-encoded address."""
        url = (
            "https://bir.no/tjenester/tommekalender/?rId=12345&name=Test%20Address%2010"
        )
        assert extract_address(url) == "Test Address 10"

    def test_extract_address_missing(self):
        """Test extracting address from URL without name."""
        url = "https://bir.no/tjenester/tommekalender/?rId=12345"
        assert extract_address(url) is None


class TestCoordinator:
    """Tests for BIRDataUpdateCoordinator."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock aiohttp session."""
        return MagicMock()

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.loop = None
        return hass

    async def test_login_success(self, mock_hass, mock_session):
        """Test successful login returns token."""
        mock_response = AsyncMock()
        mock_response.headers = {"Token": "test_token_12345"}
        mock_response.raise_for_status = MagicMock()

        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(),
            )
        )

        coordinator = BIRDataUpdateCoordinator(
            mock_hass, mock_session, "12345", "Test Address"
        )

        token = await coordinator._login()

        assert token == "test_token_12345"
        mock_session.post.assert_called_once()

    async def test_login_caches_token(self, mock_hass, mock_session):
        """Test login returns cached token when available."""
        mock_response = AsyncMock()
        mock_response.headers = {"Token": "test_token"}
        mock_response.raise_for_status = MagicMock()

        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(),
            )
        )

        coordinator = BIRDataUpdateCoordinator(
            mock_hass, mock_session, "12345", "Test Address"
        )
        coordinator._token = "cached_token"

        token = await coordinator._login()

        assert token == "cached_token"
        mock_session.post.assert_not_called()

    async def test_login_force_refresh(self, mock_hass, mock_session):
        """Test login refreshes token when force_refresh is True."""
        mock_response = AsyncMock()
        mock_response.headers = {"Token": "new_token"}
        mock_response.raise_for_status = MagicMock()

        mock_session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock(),
            )
        )

        coordinator = BIRDataUpdateCoordinator(
            mock_hass, mock_session, "12345", "Test Address"
        )
        coordinator._token = "old_token"

        token = await coordinator._login(force_refresh=True)

        assert token == "new_token"
        mock_session.post.assert_called_once()

    async def test_process_pickup_data(self, mock_hass, mock_session):
        """Test processing of pickup data."""
        coordinator = BIRDataUpdateCoordinator(
            mock_hass, mock_session, "12345", "Test Address"
        )

        raw_data = [
            {"fraksjon": "Restavfall", "dato": "2024-01-15T00:00:00"},
            {"fraksjon": "Papir", "dato": "2024-01-20T00:00:00"},
            {"fraksjon": "Matavfall", "dato": "2024-01-12T00:00:00"},
        ]

        with patch("custom_components.bir.coordinator.datetime") as mock_datetime:
            mock_datetime.today.return_value.date.return_value = datetime(
                2024, 1, 10
            ).date()
            mock_datetime.strptime = datetime.strptime

            result = coordinator._process_pickup_data(raw_data)

        assert "Mixed Waste" in result
        assert "Paper And Plastic" in result
        assert "Food Waste" in result
        assert result["Mixed Waste"]["date"] == "2024-01-15"
        assert result["Food Waste"]["days_until"] == 2

    async def test_process_pickup_data_filters_unknown_types(
        self, mock_hass, mock_session
    ):
        """Test that unknown waste types are filtered out."""
        coordinator = BIRDataUpdateCoordinator(
            mock_hass, mock_session, "12345", "Test Address"
        )

        raw_data = [
            {"fraksjon": "Restavfall", "dato": "2024-01-15T00:00:00"},
            {"fraksjon": "UnknownType", "dato": "2024-01-20T00:00:00"},
        ]

        with patch("custom_components.bir.coordinator.datetime") as mock_datetime:
            mock_datetime.today.return_value.date.return_value = datetime(
                2024, 1, 10
            ).date()
            mock_datetime.strptime = datetime.strptime

            result = coordinator._process_pickup_data(raw_data)

        assert "Mixed Waste" in result
        assert len(result) == 1
