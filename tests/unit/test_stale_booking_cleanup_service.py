"""Unit tests for stale_booking_cleanup service."""

from unittest.mock import MagicMock, call, patch

from core.services.stale_booking_cleanup import cleanup_stale_bookings


def _make_item(employee_id: str, booking_id: str, execution_arn: str = "arn:aws:states:::exec/1") -> dict:
    return {
        "employeeId": {"S": employee_id},
        "bookingId": {"S": booking_id},
        "executionArn": {"S": execution_arn},
    }


def test_empty_scan_returns_zero():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": []}

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 0}
    dynamo.update_item.assert_not_called()


def test_running_execution_is_skipped():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": [_make_item("emp-1", "book-1")]}
    sfn.describe_execution.return_value = {"status": "RUNNING"}

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 0}
    dynamo.update_item.assert_not_called()


def test_stopped_execution_is_marked_failed():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": [_make_item("emp-1", "book-1")]}
    sfn.describe_execution.return_value = {"status": "FAILED"}

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 1}
    dynamo.update_item.assert_called_once()
    call_args = dynamo.update_item.call_args[1]
    assert call_args["ExpressionAttributeValues"][":status"] == {"S": "FAILED"}


def test_empty_execution_arn_marked_failed_without_sfn_call():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": [_make_item("emp-1", "book-1", execution_arn="")]}

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 1}
    sfn.describe_execution.assert_not_called()
    dynamo.update_item.assert_called_once()


def test_describe_execution_exception_treated_as_not_running():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": [_make_item("emp-1", "book-1")]}
    sfn.describe_execution.side_effect = Exception("ExecutionDoesNotExist")

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 1}
    dynamo.update_item.assert_called_once()


def test_multiple_items_correct_count():
    dynamo = MagicMock()
    sfn = MagicMock()
    dynamo.scan.return_value = {"Items": [
        _make_item("emp-1", "book-1"),
        _make_item("emp-2", "book-2"),
        _make_item("emp-3", "book-3"),
    ]}
    sfn.describe_execution.return_value = {"status": "TIMED_OUT"}

    result = cleanup_stale_bookings(dynamo, sfn, "Bookings")

    assert result == {"resolved": 3}
    assert dynamo.update_item.call_count == 3
