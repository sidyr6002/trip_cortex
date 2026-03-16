"""Unit tests for booking_status service."""

from unittest.mock import MagicMock

from core.services.booking_status import complete_booking, create_booking


def test_create_booking_puts_correct_item():
    dynamo = MagicMock()
    create_booking(dynamo, "Bookings", "emp-1", "book-1", "conn-1")

    dynamo.put_item.assert_called_once()
    call = dynamo.put_item.call_args[1]
    item = call["Item"]
    assert item["employeeId"] == {"S": "emp-1"}
    assert item["bookingId"] == {"S": "book-1"}
    assert item["status"] == {"S": "ACTIVE"}
    assert item["connectionId"] == {"S": "conn-1"}
    assert "createdAt" in item
    assert "executionArn" in item


def test_create_booking_passes_condition_expression():
    dynamo = MagicMock()
    create_booking(dynamo, "Bookings", "emp-1", "book-1", "conn-1")

    call = dynamo.put_item.call_args[1]
    assert "ConditionExpression" in call
    assert ":active" in call["ExpressionAttributeValues"]
    assert call["ExpressionAttributeValues"][":active"] == {"S": "ACTIVE"}


def test_complete_booking_sets_completed_status():
    dynamo = MagicMock()
    complete_booking(dynamo, "Bookings", "emp-1", "book-1", "COMPLETED")

    call = dynamo.update_item.call_args[1]
    assert call["Key"] == {"employeeId": {"S": "emp-1"}, "bookingId": {"S": "book-1"}}
    assert call["ExpressionAttributeValues"][":status"] == {"S": "COMPLETED"}
    assert ":ts" in call["ExpressionAttributeValues"]


def test_complete_booking_sets_failed_status():
    dynamo = MagicMock()
    complete_booking(dynamo, "Bookings", "emp-1", "book-1", "FAILED")

    call = dynamo.update_item.call_args[1]
    assert call["ExpressionAttributeValues"][":status"] == {"S": "FAILED"}


def test_complete_booking_idempotent():
    dynamo = MagicMock()
    complete_booking(dynamo, "Bookings", "emp-1", "book-1", "COMPLETED")
    complete_booking(dynamo, "Bookings", "emp-1", "book-1", "COMPLETED")
    assert dynamo.update_item.call_count == 2  # no exception, called twice fine
