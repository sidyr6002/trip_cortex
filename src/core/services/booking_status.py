"""Booking record lifecycle — create (ACTIVE) and complete (COMPLETED/FAILED)."""

from datetime import datetime, timezone
from typing import Any, Literal


def create_booking(
    dynamo: Any,
    table: str,
    employee_id: str,
    booking_id: str,
    connection_id: str,
) -> None:
    """Write ACTIVE booking record. Raises ConditionalCheckFailedException on race condition."""
    dynamo.put_item(
        TableName=table,
        Item={
            "employeeId": {"S": employee_id},
            "bookingId": {"S": booking_id},
            "status": {"S": "ACTIVE"},
            "connectionId": {"S": connection_id},
            "executionArn": {"S": ""},
            "createdAt": {"S": datetime.now(timezone.utc).isoformat()},
        },
        ConditionExpression="attribute_not_exists(employeeId) OR #s <> :active",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":active": {"S": "ACTIVE"}},
    )


def complete_booking(
    dynamo: Any,
    table: str,
    employee_id: str,
    booking_id: str,
    status: Literal["COMPLETED", "FAILED"],
) -> None:
    """Transition booking record to a terminal status."""
    dynamo.update_item(
        TableName=table,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        UpdateExpression="SET #s = :status, completedAt = :ts",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": {"S": status},
            ":ts": {"S": datetime.now(timezone.utc).isoformat()},
        },
    )
