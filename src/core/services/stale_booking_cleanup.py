"""Stale booking cleanup — marks ACTIVE bookings older than 2 hours as FAILED."""

from datetime import datetime, timedelta, timezone
from typing import Any

from core.services.booking_status import complete_booking

_STALE_THRESHOLD_HOURS = 2


def cleanup_stale_bookings(dynamo: Any, sfn: Any, table: str) -> dict[str, int]:
    """
    Scan for ACTIVE bookings older than 2 hours. For each, check if the SFN
    execution is still running — if not (or if no executionArn), mark FAILED.
    Returns {"resolved": <count>}.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=_STALE_THRESHOLD_HOURS)).isoformat()

    resp = dynamo.scan(
        TableName=table,
        FilterExpression="#s = :active AND createdAt < :cutoff",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":active": {"S": "ACTIVE"},
            ":cutoff": {"S": cutoff},
        },
        ProjectionExpression="employeeId, bookingId, executionArn",
    )

    resolved = 0
    for item in resp.get("Items", []):
        employee_id = item["employeeId"]["S"]
        booking_id = item["bookingId"]["S"]
        execution_arn = item.get("executionArn", {}).get("S", "")

        if execution_arn and _execution_still_running(sfn, execution_arn):
            continue

        complete_booking(dynamo, table, employee_id, booking_id, "FAILED")
        resolved += 1

    return {"resolved": resolved}


def _execution_still_running(sfn: Any, execution_arn: str) -> bool:
    try:
        resp = sfn.describe_execution(executionArn=execution_arn)
        return resp["status"] == "RUNNING"
    except Exception:
        return False
