"""Integration tests for booking guard and status services against DynamoDB Local."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import boto3
import pytest

from core.services.booking_guard import check_active_booking
from core.services.booking_status import complete_booking, create_booking
from core.errors import ValidationError

TABLE = "TripCortexBookings"
ENDPOINT = "http://localhost:8000"


@pytest.fixture(scope="module")
def dynamo():
    return boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )


@pytest.fixture(autouse=True)
def cleanup(dynamo):
    """Delete test items after each test."""
    yield
    for emp in ("integ-emp-1", "integ-emp-2", "integ-emp-race"):
        resp = dynamo.query(
            TableName=TABLE,
            KeyConditionExpression="employeeId = :e",
            ExpressionAttributeValues={":e": {"S": emp}},
        )
        for item in resp.get("Items", []):
            dynamo.delete_item(
                TableName=TABLE,
                Key={"employeeId": item["employeeId"], "bookingId": item["bookingId"]},
            )


# ── booking_guard ─────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_guard_passes_when_no_bookings(dynamo):
    check_active_booking(dynamo, TABLE, "integ-emp-1")  # no exception


@pytest.mark.integration
def test_guard_passes_when_only_completed_bookings(dynamo):
    dynamo.put_item(
        TableName=TABLE,
        Item={
            "employeeId": {"S": "integ-emp-1"},
            "bookingId": {"S": "book-done"},
            "status": {"S": "COMPLETED"},
            "createdAt": {"S": datetime.now(timezone.utc).isoformat()},
        },
    )
    check_active_booking(dynamo, TABLE, "integ-emp-1")  # no exception


@pytest.mark.integration
def test_guard_blocks_when_active_booking_exists(dynamo):
    dynamo.put_item(
        TableName=TABLE,
        Item={
            "employeeId": {"S": "integ-emp-1"},
            "bookingId": {"S": "book-active"},
            "status": {"S": "ACTIVE"},
            "createdAt": {"S": datetime.now(timezone.utc).isoformat()},
        },
    )
    with pytest.raises(ValidationError):
        check_active_booking(dynamo, TABLE, "integ-emp-1")


@pytest.mark.integration
def test_filter_expression_excludes_non_active(dynamo):
    """ACTIVE + COMPLETED for same employee — guard fires only because of ACTIVE."""
    dynamo.put_item(
        TableName=TABLE,
        Item={"employeeId": {"S": "integ-emp-2"}, "bookingId": {"S": "book-done"}, "status": {"S": "COMPLETED"}, "createdAt": {"S": datetime.now(timezone.utc).isoformat()}},
    )
    dynamo.put_item(
        TableName=TABLE,
        Item={"employeeId": {"S": "integ-emp-2"}, "bookingId": {"S": "book-active"}, "status": {"S": "ACTIVE"}, "createdAt": {"S": datetime.now(timezone.utc).isoformat()}},
    )
    with pytest.raises(ValidationError):
        check_active_booking(dynamo, TABLE, "integ-emp-2")

    # Remove ACTIVE, guard should now pass
    dynamo.delete_item(TableName=TABLE, Key={"employeeId": {"S": "integ-emp-2"}, "bookingId": {"S": "book-active"}})
    check_active_booking(dynamo, TABLE, "integ-emp-2")  # no exception


# ── booking_status ────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_create_booking_writes_correct_item(dynamo):
    create_booking(dynamo, TABLE, "integ-emp-1", "book-1", "conn-1")

    resp = dynamo.get_item(
        TableName=TABLE,
        Key={"employeeId": {"S": "integ-emp-1"}, "bookingId": {"S": "book-1"}},
    )
    item = resp["Item"]
    assert item["status"]["S"] == "ACTIVE"
    assert item["connectionId"]["S"] == "conn-1"
    assert item["executionArn"]["S"] == ""
    assert "createdAt" in item


@pytest.mark.integration
def test_create_booking_race_condition_same_booking_id(dynamo):
    """Same bookingId written twice — second raises ConditionalCheckFailedException."""
    create_booking(dynamo, TABLE, "integ-emp-race", "book-1", "conn-1")

    from botocore.exceptions import ClientError
    with pytest.raises(ClientError) as exc_info:
        create_booking(dynamo, TABLE, "integ-emp-race", "book-1", "conn-2")
    assert exc_info.value.response["Error"]["Code"] == "ConditionalCheckFailedException"


@pytest.mark.integration
def test_complete_booking_transitions_status(dynamo):
    create_booking(dynamo, TABLE, "integ-emp-1", "book-1", "conn-1")
    complete_booking(dynamo, TABLE, "integ-emp-1", "book-1", "COMPLETED")

    resp = dynamo.get_item(
        TableName=TABLE,
        Key={"employeeId": {"S": "integ-emp-1"}, "bookingId": {"S": "book-1"}},
    )
    item = resp["Item"]
    assert item["status"]["S"] == "COMPLETED"
    assert "completedAt" in item


@pytest.mark.integration
def test_complete_booking_idempotent(dynamo):
    create_booking(dynamo, TABLE, "integ-emp-1", "book-1", "conn-1")
    complete_booking(dynamo, TABLE, "integ-emp-1", "book-1", "COMPLETED")
    complete_booking(dynamo, TABLE, "integ-emp-1", "book-1", "COMPLETED")  # no exception

    resp = dynamo.get_item(
        TableName=TABLE,
        Key={"employeeId": {"S": "integ-emp-1"}, "bookingId": {"S": "book-1"}},
    )
    assert resp["Item"]["status"]["S"] == "COMPLETED"


@pytest.mark.integration
def test_guard_passes_after_complete(dynamo):
    """After completing a booking, the same employee can start a new one."""
    create_booking(dynamo, TABLE, "integ-emp-1", "book-1", "conn-1")
    complete_booking(dynamo, TABLE, "integ-emp-1", "book-1", "COMPLETED")
    check_active_booking(dynamo, TABLE, "integ-emp-1")  # no exception
