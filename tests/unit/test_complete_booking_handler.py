"""Unit tests for complete_booking Lambda handler."""

from unittest.mock import MagicMock, patch


def _make_event(status: str | None = None) -> dict:
    event = {"employee_id": "emp-1", "booking_id": "book-1"}
    if status is not None:
        event["status"] = status
    return event


@patch("handlers.complete_booking.get_dynamo_client")
@patch("handlers.complete_booking.get_config")
def test_handler_calls_complete_booking(mock_config, mock_dynamo):
    from handlers.complete_booking import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")

    handler(_make_event("COMPLETED"), MagicMock())

    mock_dynamo.return_value.update_item.assert_called_once()
    call = mock_dynamo.return_value.update_item.call_args[1]
    assert call["Key"] == {"employeeId": {"S": "emp-1"}, "bookingId": {"S": "book-1"}}
    assert call["ExpressionAttributeValues"][":status"] == {"S": "COMPLETED"}


@patch("handlers.complete_booking.get_dynamo_client")
@patch("handlers.complete_booking.get_config")
def test_handler_returns_event(mock_config, mock_dynamo):
    from handlers.complete_booking import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")
    event = _make_event("FAILED")

    result = handler(event, MagicMock())

    assert result is event


@patch("handlers.complete_booking.get_dynamo_client")
@patch("handlers.complete_booking.get_config")
def test_handler_defaults_status_to_completed(mock_config, mock_dynamo):
    from handlers.complete_booking import handler

    mock_config.return_value = MagicMock(bookings_table="Bookings")

    handler(_make_event(), MagicMock())  # no status field

    call = mock_dynamo.return_value.update_item.call_args[1]
    assert call["ExpressionAttributeValues"][":status"] == {"S": "COMPLETED"}
