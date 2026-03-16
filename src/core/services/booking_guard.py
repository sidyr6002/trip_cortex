"""Single-active-booking guard — ADR-007."""

from typing import Any

from core.errors import ErrorCode, ValidationError


def check_active_booking(dynamo: Any, table: str, employee_id: str) -> None:
    """Raise ValidationError if employee already has an ACTIVE booking."""
    resp = dynamo.query(
        TableName=table,
        KeyConditionExpression="employeeId = :eid",
        FilterExpression="#s = :active",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":eid": {"S": employee_id},
            ":active": {"S": "ACTIVE"},
        },
        Limit=1,
    )
    if resp.get("Count", 0) > 0:
        raise ValidationError(
            "Active booking already in progress",
            code=ErrorCode.VALIDATION_ERROR,
        )
