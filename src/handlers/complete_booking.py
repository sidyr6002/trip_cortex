"""Lambda handler — marks a booking COMPLETED or FAILED at workflow end."""

from typing import Any

from core.clients import get_dynamo_client
from core.config import get_config
from core.services.booking_status import complete_booking


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    complete_booking(
        get_dynamo_client(),
        config.bookings_table,
        event["employee_id"],
        event["booking_id"],
        event.get("status", "COMPLETED"),
    )
    return event
