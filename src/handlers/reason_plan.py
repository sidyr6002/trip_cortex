"""Lambda handler for reasoning and booking plan generation."""

from typing import Any

from core.clients import get_dynamo_client, get_reasoning_service
from core.config import get_config
from core.models.booking import ReasoningRequest
from core.services.audit import build_reasoning_audit_entry, write_audit_log


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    request = ReasoningRequest.model_validate(event)
    result = get_reasoning_service().generate_booking_plan(request, context.get_remaining_time_in_millis())

    write_audit_log(
        get_dynamo_client(),
        config.audit_log_table,
        build_reasoning_audit_entry(
            booking_id=result.booking_id,
            employee_id=result.employee_id,
            model_id=result.model_id,
            thinking_effort=result.thinking_effort,
            latency_ms=result.latency_ms,
            retry_count=result.retry_count,
            escalated=result.escalated,
            plan_confidence=result.plan.confidence,
            plan_intent=result.plan.intent,
            warnings_count=len(result.plan.warnings),
        ),
    )

    return result.model_dump(mode="json")
