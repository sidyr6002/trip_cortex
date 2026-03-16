"""Unit tests for circuit breaker integration in the flight booking handler."""

from unittest.mock import MagicMock, patch

import pytest

from core.errors import PortalUnavailableError


def _make_cb(can_execute: bool = True) -> MagicMock:
    cb = MagicMock()
    cb.can_execute.return_value = can_execute
    return cb


def _booking_event() -> dict:
    return {
        "booking_id": "b-1",
        "employee_id": "emp-1",
        "selected_flight": {"flight": {}, "passengers": [], "search_url": "https://example.com"},
        "validated_result": {"plan": {}},
    }


# ── invoke_flight_booking ────────────────────────────────────────────────────


@patch("handlers.invoke_flight_booking.get_circuit_breaker_service")
@patch("handlers.invoke_flight_booking.invoke_acr_workflow", return_value={})
@patch("handlers.invoke_flight_booking.get_acr_client")
@patch("handlers.invoke_flight_booking.get_config")
def test_booking_circuit_open_raises_portal_unavailable(mock_cfg, mock_acr, mock_invoke, mock_cb_factory) -> None:
    mock_cb_factory.return_value = _make_cb(can_execute=False)
    from handlers.invoke_flight_booking import handler
    with pytest.raises(PortalUnavailableError):
        handler(_booking_event(), None)
    mock_invoke.assert_not_called()


@patch("handlers.invoke_flight_booking.get_circuit_breaker_service")
@patch("handlers.invoke_flight_booking.invoke_acr_workflow", return_value={})
@patch("handlers.invoke_flight_booking.get_acr_client")
@patch("handlers.invoke_flight_booking.get_config")
def test_booking_uses_lower_threshold(mock_cfg, mock_acr, mock_invoke, mock_cb_factory) -> None:
    cb = _make_cb(can_execute=True)
    mock_cb_factory.return_value = cb
    from handlers.invoke_flight_booking import handler
    handler(_booking_event(), None)
    mock_cb_factory.assert_called_once_with(failure_threshold=3, recovery_timeout=60)
