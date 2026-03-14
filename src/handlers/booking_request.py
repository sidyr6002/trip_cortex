"""Lambda handler — starts booking workflow or resumes HITL on flight selection."""

import json
from typing import Any

from core.clients import get_dynamo_client, get_sfn_client
from core.config import get_config
from core.services.task_token import pop_task_token


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

    # Initial request — start Step Functions execution
    get_sfn_client().start_execution(
        stateMachineArn=config.booking_workflow_arn,
        input=json.dumps({
            "connection_id": connection_id,
            "booking_id": body["booking_id"],
            "employee_id": body["employee_id"],
            "user_query": body["user_query"],
        }),
    )
    return {"statusCode": 200}
