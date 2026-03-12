"""Lambda handler for BookingPlan validation — defense-in-depth gate."""

from typing import Any

from core.models.booking import ReasoningResult
from core.services.plan_validation import validate_plan


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    result = ReasoningResult.model_validate(event)
    validated = validate_plan(result)
    return validated.model_dump(mode="json")
