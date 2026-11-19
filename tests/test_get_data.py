"""Test BIR Waste Watch coordinator module."""

from datetime import datetime
import logging
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import ClientResponseError
from homeassistant.helpers.update_coordinator import UpdateFailed
import pytest

from custom_components.bir.coordinator import (
    BIRDataUpdateCoordinator,
    BIRTokenStorage,
    async_search_addresses,
    extract_address,
    extract_property_id,
)


def _mock_get_response(status: int, payload: list | None = None) -> AsyncMock:
    """Build a mocked aiohttp GET context manager with the given status."""
    response = AsyncMock()
    response.status = status
    response.json = AsyncMock(return_value=payload or [])
    if status >= 400:
        response.raise_for_status = MagicMock(
            side_effect=ClientResponseError(MagicMock(), (), status=status)
        )
    else:
        response.raise_for_status = MagicMock()
    return AsyncMock(
        __aenter__=AsyncMock(return_value=response),
        __aexit__=AsyncMock(return_value=False),
    )


def _mock_login_response(token: str = "fresh_token") -> AsyncMock:
    """Build a mocked aiohttp POST context manager for login."""
    response = AsyncMock()
    response.headers = {"Token": token}
    response.raise_for_status = MagicMock()
    return AsyncMock(
        __aenter__=AsyncMock(return_value=response),
        __aexit__=AsyncMock(return_value=False),
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


class TestTokenExpiry:
    """BIR answers 500 for an expired token; only a failed retry is an error."""

    PICKUP = [{"fraksjon": "Restavfall", "dato": "2099-01-15T00:00:00"}]

    @pytest.fixture
    def coordinator(self):
        """Coordinator with a stale cached token."""
        session = MagicMock()
        session.post = MagicMock(return_value=_mock_login_response())
        coordinator = BIRDataUpdateCoordinator(
            MagicMock(), session, "12345", "Test Address"
        )
        coordinator._token = "expired_token"
        return coordinator

    async def test_expired_token_retry_succeeds_without_error_log(
        self, coordinator, caplog
    ):
        """A 500 followed by a successful retry returns data and logs no ERROR."""
        coordinator.session.get = MagicMock(
            side_effect=[
                _mock_get_response(500),
                _mock_get_response(200, self.PICKUP),
            ]
        )

        with caplog.at_level(logging.DEBUG, logger="custom_components.bir"):
            result = await coordinator._async_update_data()

        assert "Mixed Waste" in result
        assert coordinator._token == "fresh_token"
        coordinator.session.post.assert_called_once()
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]

    async def test_500_after_fresh_login_raises_update_failed(
        self, coordinator, caplog
    ):
        """A 500 on the retry is a real failure and names the property."""
        coordinator.session.get = MagicMock(
            side_effect=[_mock_get_response(500), _mock_get_response(500)]
        )

        with (
            caplog.at_level(logging.DEBUG, logger="custom_components.bir"),
            pytest.raises(UpdateFailed, match="12345.*after a fresh login"),
        ):
            await coordinator._async_update_data()

        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]

    async def test_login_500_is_not_reported_as_property_error(self, coordinator):
        """A 500 from the login endpoint must not blame the property ID."""
        login_response = AsyncMock()
        login_response.raise_for_status = MagicMock(
            side_effect=ClientResponseError(MagicMock(), (), status=500)
        )
        coordinator.session.post = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=login_response),
                __aexit__=AsyncMock(return_value=False),
            )
        )
        coordinator.session.get = MagicMock(side_effect=[_mock_get_response(500)])

        with pytest.raises(UpdateFailed) as exc_info:
            await coordinator._async_update_data()

        assert "after a fresh login" not in str(exc_info.value)
        assert "Error communicating with BIR API" in str(exc_info.value)


@pytest.mark.parametrize("status", [401, 500])
async def test_connection_refreshes_expired_token(status: int) -> None:
    """Connection validation retries on authentication failures from BIR."""
    session = MagicMock()
    session.post = MagicMock(return_value=_mock_login_response())
    session.get = MagicMock(
        side_effect=[_mock_get_response(status), _mock_get_response(200)]
    )
    storage = MagicMock()
    storage.async_clear_token = AsyncMock()
    storage.async_save_token = AsyncMock()
    coordinator = BIRDataUpdateCoordinator(
        MagicMock(), session, "12345", "Test Address", token_storage=storage
    )
    coordinator._token = "stale_token"

    assert await coordinator.async_test_connection()
    assert coordinator._token == "fresh_token"
    assert session.get.call_count == 2
    storage.async_clear_token.assert_awaited_once_with("12345")
    storage.async_save_token.assert_awaited_once_with("12345", "fresh_token")


async def test_connection_does_not_retry_other_http_errors() -> None:
    """Only authentication-related failures justify a fresh login."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_get_response(403))
    coordinator = BIRDataUpdateCoordinator(MagicMock(), session, "12345", "Address")
    coordinator._token = "valid_token"

    with pytest.raises(ClientResponseError) as exc_info:
        await coordinator.async_test_connection()

    assert exc_info.value.status == 403
    session.get.assert_called_once()


@pytest.mark.parametrize(
    ("status", "message"),
    [(504, "not responding"), (403, "Error communicating with BIR API")],
)
async def test_update_reports_http_failures(status: int, message: str) -> None:
    """Expose a useful error for timeouts and other HTTP failures."""
    session = MagicMock()
    session.get = MagicMock(return_value=_mock_get_response(status))
    coordinator = BIRDataUpdateCoordinator(MagicMock(), session, "12345", "Address")
    coordinator._token = "valid_token"

    with pytest.raises(UpdateFailed, match=message):
        await coordinator._async_update_data()

    session.get.assert_called_once()


async def test_update_wraps_unexpected_errors() -> None:
    """Unexpected network errors become coordinator update failures."""
    coordinator = BIRDataUpdateCoordinator(MagicMock(), MagicMock(), "12345", "Address")
    coordinator._token = "valid_token"
    with (
        patch.object(
            coordinator, "_fetch_pickup_dates", side_effect=ConnectionError("offline")
        ),
        pytest.raises(UpdateFailed, match="Unexpected error: offline"),
    ):
        await coordinator._async_update_data()


async def test_cached_token_and_missing_login_token() -> None:
    """Load saved tokens and report an invalid login response."""
    storage = MagicMock()
    storage.async_get_token = AsyncMock(return_value="saved_token")
    session = MagicMock()
    session.post = MagicMock(return_value=_mock_login_response(token=""))
    coordinator = BIRDataUpdateCoordinator(
        MagicMock(), session, "12345", "Address", token_storage=storage
    )

    await coordinator.async_initialize()
    assert coordinator._token == "saved_token"
    storage.async_get_token.assert_awaited_once_with("12345")

    coordinator._token = None
    with pytest.raises(UpdateFailed, match="Token not found"):
        await coordinator._login()


async def test_search_addresses_filters_entries_without_ids() -> None:
    """Map BIR's search response to selectable address entries."""
    response = AsyncMock()
    response.raise_for_status = MagicMock()
    response.json = AsyncMock(
        return_value=[
            {"Id": "12345", "Title": "Testveien 1", "SubTitle": "Bergen"},
            {"Id": None, "Title": "Missing ID"},
        ]
    )
    session = MagicMock()
    session.get = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=response),
            __aexit__=AsyncMock(return_value=False),
        )
    )

    assert await async_search_addresses(session, "Testveien") == [
        {"id": "12345", "adresse": "Testveien 1, Bergen"}
    ]
    assert session.get.call_args.kwargs["params"]["q"] == "Testveien"


async def test_token_storage_load_save_and_clear() -> None:
    """Persist newly issued tokens and remove them when they expire."""
    store = MagicMock()
    store.async_load = AsyncMock(return_value={"12345": "saved_token"})
    store.async_save = AsyncMock()
    with patch("custom_components.bir.coordinator.Store", return_value=store):
        storage = BIRTokenStorage(MagicMock())

    await storage.async_load()
    assert await storage.async_get_token("12345") == "saved_token"
    await storage.async_save_token("12345", "fresh_token")
    assert await storage.async_get_token("12345") == "fresh_token"
    await storage.async_clear_token("12345")
    assert await storage.async_get_token("12345") is None
    assert store.async_save.await_count == 2
    assert store.async_save.await_args.args == ({},)


async def test_retry_propagates_non_500_http_error() -> None:
    """Report a retry failure other than 500 as a normal HTTP error."""
    session = MagicMock()
    session.post = MagicMock(return_value=_mock_login_response())
    session.get = MagicMock(
        side_effect=[_mock_get_response(401), _mock_get_response(403)]
    )
    coordinator = BIRDataUpdateCoordinator(MagicMock(), session, "12345", "Address")
    coordinator._token = "expired_token"

    with pytest.raises(UpdateFailed, match="Error communicating with BIR API"):
        await coordinator._async_update_data()
    assert session.get.call_count == 2
