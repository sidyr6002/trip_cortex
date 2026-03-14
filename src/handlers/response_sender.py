"""Lambda handler — sends flight options to client via WebSocket and stores HITL task token."""

import json
from typing import Any

from core.clients import get_apigw_client, get_dynamo_client
from core.config import get_config
from core.services.task_token import store_task_token


def handler(event: dict[str, Any], context: Any) -> None:
    config = get_config()

    store_task_token(
        get_dynamo_client(),
        config.bookings_table,
        event["booking_id"],
        event["employee_id"],
        event["task_token"],
    )

    get_apigw_client().post_to_connection(
        ConnectionId=event["connection_id"],
        Data=json.dumps({
            "type": "flight_options",
            "booking_id": event["booking_id"],
            "flights": event["flights"],
        }).encode(),
    )
