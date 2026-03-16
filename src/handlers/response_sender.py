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

    if msg_type == "progress":
        payload = {
            "type": "progress",
            "booking_id": event.get("booking_id"),
            "payload": {"message": event.get("message", "")},
        }
    elif msg_type == "flight_options":
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
    elif msg_type == "payment_confirmation":
        store_task_token(
            get_dynamo_client(),
            config.bookings_table,
            event["booking_id"],
            event["employee_id"],
            event["task_token"],
        )
        payload = {
            "type": "payment_confirmation",
            "booking_id": event["booking_id"],
            "flight": event["flight"],
            "passengers": event["passengers"],
        }
    elif msg_type == "booking_complete":
        payload = {
            "type": "booking_complete",
            "booking_id": event["booking_id"],
            "confirmation": event.get("confirmation"),
        }
    elif msg_type == "fallback":
        payload = {
            "type": "fallback",
            "booking_id": event["booking_id"],
            "message": (
                "We couldn't complete your booking automatically. "
                "You can finish it manually using the link below."
            ),
            "fallback_url": event.get("fallback_url"),
            "warnings": event.get("warnings", []),
        }
    elif msg_type == "error":
        payload = {
            "type": "error",
            "booking_id": event.get("booking_id"),
            "message": event.get("message", "Something went wrong with your booking request. Please try again."),
        }
    else:
        logger.warning("response_sender unknown message type: %s", msg_type)
        payload = {
            "type": "error",
            "booking_id": event.get("booking_id"),
            "message": "Something went wrong with your booking request. Please try again.",
        }

    connection_id = event["connection_id"]
    data = json.dumps(payload).encode()
    apigw = get_apigw_client()

    try:
        apigw.post_to_connection(ConnectionId=connection_id, Data=data)
    except Exception:
        logger.warning("post_to_connection failed for %s, looking up fresh connection", connection_id)
        # Connection may have rotated during long Nova Act runs — fetch latest from bookings table
        fresh_id = _get_fresh_connection(event.get("booking_id"), event.get("employee_id"), config)
        if fresh_id and fresh_id != connection_id:
            try:
                apigw.post_to_connection(ConnectionId=fresh_id, Data=data)
            except Exception:
                logger.warning("retry post_to_connection also failed for %s", fresh_id)


def _get_fresh_connection(booking_id: str | None, employee_id: str | None, config: Any) -> str | None:
    if not booking_id or not employee_id:
        return None
    try:
        resp = get_dynamo_client().get_item(
            TableName=config.bookings_table,
            Key={"employeeId": {"S": employee_id}, "bookingId": {"S": booking_id}},
            ProjectionExpression="connectionId",
        )
        return resp.get("Item", {}).get("connectionId", {}).get("S")
    except Exception:
        logger.exception("Failed to look up fresh connection")
        return None
