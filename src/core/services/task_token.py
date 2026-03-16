"""Task token storage for Step Functions HITL (.waitForTaskToken) pattern."""

from time import time
from typing import Any


def store_task_token(dynamo_client: Any, table: str, booking_id: str, employee_id: str, task_token: str) -> None:
    """Store task token in BookingsTable with 2-hour TTL."""
    ttl = int(time()) + 7200
    dynamo_client.update_item(
        TableName=table,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        UpdateExpression="SET taskToken = :t, #ttl = :e",
        ExpressionAttributeNames={"#ttl": "ttl"},
        ExpressionAttributeValues={":t": {"S": task_token}, ":e": {"N": str(ttl)}},
    )


def pop_task_token(dynamo_client: Any, table: str, booking_id: str, employee_id: str) -> str:
    """Read and clear the task token (one-time use). Raises KeyError if not found."""
    resp = dynamo_client.get_item(
        TableName=table,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        ProjectionExpression="taskToken",
    )
    item = resp.get("Item", {})
    if "taskToken" not in item:
        raise KeyError(f"No task token for booking {booking_id}")
    token: str = item["taskToken"]["S"]
    dynamo_client.update_item(
        TableName=table,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        UpdateExpression="REMOVE taskToken",
    )
    return token
