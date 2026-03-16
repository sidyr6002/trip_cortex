"""Lambda handler — starts booking workflow or resumes HITL on flight selection."""

import json
import re
from typing import Any

from core.clients import get_dynamo_client, get_sfn_client
from core.config import get_config
from core.errors import ErrorCode, ValidationError
from core.services.booking_guard import check_active_booking
from core.services.booking_status import complete_booking, create_booking
from core.services.task_token import pop_task_token

_SFN_NAME_RE = re.compile(r"^[a-zA-Z0-9\-_]{1,74}$")  # leaves room for "booking-" prefix (8 chars) → total ≤ 80


def _validate_booking_id(booking_id: str) -> None:
    if not _SFN_NAME_RE.match(booking_id):
        raise ValidationError("Invalid booking ID format", code=ErrorCode.INVALID_REQUEST)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    body = json.loads(event.get("body") or "{}")
    connection_id = event["requestContext"]["connectionId"]

    if body.get("action") == "select_flight":
        # HITL resume — user selected a flight
        token = pop_task_token(
            get_dynamo_client(),
            config.bookings_table,
            body["booking_id"],
            body["employee_id"],
        )
        get_sfn_client().send_task_success(
            taskToken=token,
            output=json.dumps({
                "flight": body["flight"],
                "passengers": body["passengers"],
                "search_url": body["search_url"],
            }),
        )
        return {"statusCode": 200}

    # Initial request — guard against concurrent active bookings
    employee_id = body["employee_id"]
    booking_id = body["booking_id"]
    dynamo = get_dynamo_client()

    try:
        _validate_booking_id(booking_id)
        check_active_booking(dynamo, config.bookings_table, employee_id)
    except ValidationError as exc:
        return {"statusCode": 409, "body": exc.user_message}

    # Write booking record with conditional put to handle race condition
    execution_arn = ""
    try:
        create_booking(dynamo, config.bookings_table, employee_id, booking_id, connection_id)
    except dynamo.exceptions.ConditionalCheckFailedException:
        return {"statusCode": 409, "body": "You already have an active booking in progress"}

    # Start Step Functions execution
    try:
        resp = get_sfn_client().start_execution(
            stateMachineArn=config.booking_workflow_arn,
            name=f"booking-{booking_id}",
            input=json.dumps({
                "connection_id": connection_id,
                "booking_id": booking_id,
                "employee_id": employee_id,
                "user_query": body["user_query"],
            }),
        )
        execution_arn = resp["executionArn"]
    except Exception:
        # Roll back booking record so employee isn't permanently blocked
        complete_booking(dynamo, config.bookings_table, employee_id, booking_id, "FAILED")
        raise

    # Persist executionArn now that we have it
    dynamo.update_item(
        TableName=config.bookings_table,
        Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
        UpdateExpression="SET executionArn = :arn",
        ExpressionAttributeValues={":arn": {"S": execution_arn}},
    )

    return {"statusCode": 200, "body": json.dumps({"bookingId": booking_id})}
