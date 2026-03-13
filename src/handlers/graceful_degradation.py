"""Lambda handler for graceful degradation — applies strict defaults when reasoning fails."""

from typing import Any

from core.clients import get_dynamo_client
from core.config import get_config
from core.services.audit import build_degradation_audit_entry, write_audit_log
from core.services.graceful_degradation import apply_graceful_degradation


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    result = apply_graceful_degradation(
        booking_id=event["booking_id"],
        employee_id=event["employee_id"],
        user_query=event.get("user_query", ""),
        error=event.get("error", ""),
        cause=event.get("cause", ""),
    )

    write_audit_log(
        get_dynamo_client(),
        config.audit_log_table,
        build_degradation_audit_entry(
            booking_id=result.booking_id,
            employee_id=result.employee_id,
            error_code=event.get("error", "UNKNOWN"),
            original_error_message=event.get("cause", ""),
        ),
    )

    return result.model_dump(mode="json")
