"""Unit tests for the response_sender Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock, call, patch


def _make_event(msg_type: str, extra: dict | None = None) -> dict[str, Any]:
    base: dict[str, Any] = {
        "type": msg_type,
        "connection_id": "conn-abc",
        "booking_id": "book-1",
        "employee_id": "emp-1",
    }
    if extra:
        base.update(extra)
    return base


def _sent_payload(mock_apigw: MagicMock) -> dict:
    data = mock_apigw.return_value.post_to_connection.call_args[1]["Data"]
    return json.loads(data)


@patch("handlers.response_sender.store_task_token")
@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_flight_options_stores_token_and_sends(mock_config, mock_dynamo, mock_apigw, mock_store):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("flight_options", {"task_token": "tok-xyz", "flights": [{"id": "f1"}]})

    handler(event, MagicMock())

    mock_store.assert_called_once_with(
        mock_dynamo.return_value, "Bookings", "book-1", "emp-1", "tok-xyz"
    )
    payload = _sent_payload(mock_apigw)
    assert payload["type"] == "flight_options"
    assert payload["flights"] == [{"id": "f1"}]
    assert payload["booking_id"] == "book-1"


@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_booking_complete_sends_confirmation(mock_config, mock_dynamo, mock_apigw):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("booking_complete", {"confirmation": {"ref": "PNR123"}})

    handler(event, MagicMock())

    payload = _sent_payload(mock_apigw)
    assert payload["type"] == "booking_complete"
    assert payload["confirmation"] == {"ref": "PNR123"}


@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_fallback_sends_url_and_warnings(mock_config, mock_dynamo, mock_apigw):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("fallback", {"fallback_url": "https://portal/book", "warnings": ["no seats"]})

    handler(event, MagicMock())

    payload = _sent_payload(mock_apigw)
    assert payload["type"] == "fallback"
    assert payload["fallback_url"] == "https://portal/book"
    assert payload["warnings"] == ["no seats"]
    # No AWS ARNs in payload
    assert "arn:aws" not in json.dumps(payload).lower()


@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_error_sends_message(mock_config, mock_dynamo, mock_apigw):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("error", {"message": "Booking failed"})

    handler(event, MagicMock())

    payload = _sent_payload(mock_apigw)
    assert payload["type"] == "error"
    assert payload["message"] == "Booking failed"
    # No stack traces or ARNs
    assert "Traceback" not in payload["message"]


@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_unknown_type_sends_generic_error(mock_config, mock_dynamo, mock_apigw):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("unknown_type")

    handler(event, MagicMock())

    payload = _sent_payload(mock_apigw)
    assert payload["type"] == "error"
    assert "message" in payload
    assert "arn:aws" not in json.dumps(payload).lower()


@patch("handlers.response_sender.get_apigw_client")
@patch("handlers.response_sender.get_dynamo_client")
@patch("handlers.response_sender.get_config")
def test_gone_connection_logs_warning(mock_config, mock_dynamo, mock_apigw):
    from handlers.response_sender import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    mock_apigw.return_value.post_to_connection.side_effect = Exception("GoneException")

    # Must not raise
    handler(_make_event("error", {"message": "oops"}), MagicMock())
