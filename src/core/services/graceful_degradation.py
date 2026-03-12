"""Graceful degradation service — applies strictest defaults when reasoning fails."""

from datetime import date

import structlog

from core.models.booking import BookingPlan, ReasoningResult

logger = structlog.get_logger()


def apply_graceful_degradation(
    booking_id: str,
    employee_id: str,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str | None = None,
    error: str = "",
    cause: str = "",
) -> ReasoningResult:
    """Return a ReasoningResult built from strict defaults when reasoning has failed.

    Args:
        booking_id: Booking identifier for traceability.
        employee_id: Employee identifier for traceability.
        origin: IATA origin code from the upstream EmbedAndRetrieve output.
        destination: IATA destination code.
        departure_date: ISO 8601 date string (YYYY-MM-DD).
        return_date: ISO 8601 date string or None.
        error: Step Functions error name (logged server-side only).
        cause: Step Functions error cause (logged server-side only).
    """
    logger.warning(
        "graceful_degradation_applied",
        booking_id=booking_id,
        error=error,
    )

    plan = BookingPlan.strict_defaults(
        origin=origin,
        destination=destination,
        departure_date=date.fromisoformat(departure_date),
        return_date=date.fromisoformat(return_date) if return_date else None,
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
