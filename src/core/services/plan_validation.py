"""Plan validation service — defense-in-depth checks on the BookingPlan from reasoning."""

from datetime import date

import structlog

from core.errors import ErrorCode, ValidationError
from core.models.booking import ReasoningResult

logger = structlog.get_logger()


def validate_plan(result: ReasoningResult) -> ReasoningResult:
    """Re-validate the BookingPlan and run business rule checks.

    Adds warnings for soft violations. Raises ValidationError for hard violations.
    Returns the (possibly amended) ReasoningResult.
    """
    plan = result.plan
    warnings = list(plan.warnings)

    # Hard check: departure date must still be in the future at validation time.
    if plan.parameters.departure_date < date.today():
        raise ValidationError(
            "departure_date is in the past at validation time",
            code=ErrorCode.INVALID_PLAN,
        )

    # Soft check: advance booking requirement.
    adv = plan.policy_constraints.advance_booking_days_required
    if adv is not None:
        days_until = (plan.parameters.departure_date - date.today()).days
        if days_until < adv and plan.policy_constraints.advance_booking_met:
            # LLM incorrectly marked advance_booking_met as True — correct it.
            plan.policy_constraints.advance_booking_met = False
            warnings.append(f"ADVANCE_BOOKING_NOT_MET: {days_until} days < {adv} required")

    # Soft check: low confidence plans should require approval.
    if plan.confidence < 0.5 and not plan.policy_constraints.requires_approval:
        plan.policy_constraints.requires_approval = True
        plan.policy_constraints.approval_reason = "Low confidence plan — auto-flagged for review"
        warnings.append("LOW_CONFIDENCE_APPROVAL_REQUIRED")

    if warnings != plan.warnings:
        plan.warnings = warnings
        logger.info("plan_validation_amended", booking_id=result.booking_id, new_warnings=warnings)

    return result
