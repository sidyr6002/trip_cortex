"""Unit tests for booking_guard service."""

from unittest.mock import MagicMock

import pytest

from core.errors import ValidationError
from core.services.booking_guard import check_active_booking


def test_guard_passes_when_count_zero():
    dynamo = MagicMock()
    dynamo.query.return_value = {"Count": 0}
    check_active_booking(dynamo, "Bookings", "emp-1")  # no exception


def test_guard_raises_when_count_nonzero():
    dynamo = MagicMock()
    dynamo.query.return_value = {"Count": 1}
    with pytest.raises(ValidationError) as exc_info:
        check_active_booking(dynamo, "Bookings", "emp-1")
    assert exc_info.value.code.value == "VALIDATION_ERROR"


def test_guard_query_uses_correct_expressions():
    dynamo = MagicMock()
    dynamo.query.return_value = {"Count": 0}

    check_active_booking(dynamo, "Bookings", "emp-1")

    call = dynamo.query.call_args[1]
    assert call["TableName"] == "Bookings"
    assert "employeeId" in call["KeyConditionExpression"]
    assert ":eid" in call["ExpressionAttributeValues"]
    assert call["ExpressionAttributeValues"][":eid"] == {"S": "emp-1"}
    assert call["ExpressionAttributeValues"][":active"] == {"S": "ACTIVE"}
    assert "#s" in call["ExpressionAttributeNames"]
    assert call["ExpressionAttributeNames"]["#s"] == "status"
    assert call["Limit"] == 1
