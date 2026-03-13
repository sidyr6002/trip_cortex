"""Graceful degradation service — applies strictest defaults when reasoning fails."""

from datetime import date, timedelta

import structlog

from core.models.booking import BookingPlan, ReasoningResult

logger = structlog.get_logger()


def apply_graceful_degradation(
    booking_id: str,
    employee_id: str,
    user_query: str = "",
    error: str = "",
    cause: str = "",
) -> ReasoningResult:
    """Return a ReasoningResult built from strict defaults when reasoning has failed.

    Uses placeholder airport codes and a 30-day-out departure date since the
    structured parameters were never extracted (reasoning failed before producing them).
    The plan requires mandatory human approval, so the placeholders will be corrected
    during the HITL review step.
    """
    logger.warning(
        "graceful_degradation_applied",
        booking_id=booking_id,
        error=error,
    )

    plan = BookingPlan.strict_defaults(
        origin="ZZZ",
        destination="ZZY",
        departure_date=date.today() + timedelta(days=30),
    )

    return ReasoningResult(
        booking_id=booking_id,
        employee_id=employee_id,
        plan=plan,
        model_id="strict-defaults",
        thinking_effort="medium",
        latency_ms=0.0,
        retry_count=0,
        escalated=False,
    )
