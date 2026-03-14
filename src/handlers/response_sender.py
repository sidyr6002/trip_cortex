"""Lambda handler — sends WebSocket messages and stores HITL task token."""

import json
import logging
from typing import Any

from core.clients import get_apigw_client, get_dynamo_client
from core.config import get_config
from core.services.task_token import store_task_token

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> None:
    config = get_config()
    msg_type = event.get("type")

    if msg_type == "flight_options":
        store_task_token(
            get_dynamo_client(),
            config.bookings_table,
            event["booking_id"],
            event["employee_id"],
            event["task_token"],
        )
        payload = {
            "type": "flight_options",
            "booking_id": event["booking_id"],
            "flights": event["flights"],
        }
    else:
        # booking_complete
        payload = {
            "type": "booking_complete",
            "booking_id": event["booking_id"],
            "confirmation": event.get("confirmation"),
        }

    try:
        get_apigw_client().post_to_connection(
            ConnectionId=event["connection_id"],
            Data=json.dumps(payload).encode(),
        )
    except Exception:
        logger.warning("post_to_connection failed for %s", event["connection_id"])
