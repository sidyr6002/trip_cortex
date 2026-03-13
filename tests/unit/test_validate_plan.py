"""Unit tests for plan validation service and handler."""

from datetime import date, timedelta
from typing import Any
from unittest.mock import patch

import pytest

from core.errors import ErrorCode, ValidationError
from core.models.booking import (
    BookingParameters,
    BookingPlan,
    PolicyConstraints,
    PolicySource,
    ReasoningResult,
)
from core.services.plan_validation import validate_plan

FUTURE = date.today() + timedelta(days=30)
FUTURE2 = date.today() + timedelta(days=37)


def _make_result(**plan_overrides: Any) -> ReasoningResult:
    plan_kwargs: dict[str, Any] = {
        "intent": "flight_booking",
        "confidence": 0.92,
        "parameters": BookingParameters(
            origin="HYD", destination="ORD", departure_date=FUTURE, return_date=FUTURE2, cabin_class="economy"
        ),
        "policy_constraints": PolicyConstraints(
            max_budget_usd=500.0,
            preferred_vendors=["Delta", "United"],
            advance_booking_days_required=14,
            advance_booking_met=True,
        ),
        "policy_sources": [PolicySource(chunk_id="c-1", section_title="Air Travel", page=3, similarity_score=0.89)],
        "reasoning_summary": "Economy, $500 cap.",
    }
    plan_kwargs.update(plan_overrides)
    return ReasoningResult(
        booking_id="b-1",
        employee_id="e-1",
        plan=BookingPlan(**plan_kwargs),
        model_id="us.amazon.nova-2-lite-v1:0",
        thinking_effort="medium",
        latency_ms=1500.0,
    )


class TestValidatePlan:
    def test_valid_plan_passes_through(self):
        result = _make_result()
        validated = validate_plan(result)
        assert validated.plan.warnings == []

    def test_past_departure_raises(self):
        result = _make_result(
            parameters=BookingParameters(
                origin="HYD",
                destination="ORD",
                departure_date=date.today() + timedelta(days=1),
                cabin_class="economy",
            ),
        )
        # Force the date to the past after construction (bypass Pydantic validator).
        result.plan.parameters.departure_date = date.today() - timedelta(days=1)

        with pytest.raises(ValidationError, match="departure_date is in the past") as exc_info:
            validate_plan(result)
        assert exc_info.value.code == ErrorCode.INVALID_PLAN

    def test_advance_booking_not_met_corrected(self):
        # Departure is 5 days out, policy requires 14 days, LLM said advance_booking_met=True.
        result = _make_result(
            parameters=BookingParameters(
                origin="HYD",
                destination="ORD",
                departure_date=date.today() + timedelta(days=5),
                cabin_class="economy",
            ),
            policy_constraints=PolicyConstraints(
                max_budget_usd=500.0,
                preferred_vendors=["Delta"],
                advance_booking_days_required=14,
                advance_booking_met=True,
            ),
        )

        validated = validate_plan(result)

        assert validated.plan.policy_constraints.advance_booking_met is False
        assert any("ADVANCE_BOOKING_NOT_MET" in w for w in validated.plan.warnings)

    def test_advance_booking_met_not_touched_when_correct(self):
        result = _make_result()  # 30 days out, 14 required — correctly True
        validated = validate_plan(result)
        assert validated.plan.policy_constraints.advance_booking_met is True
        assert validated.plan.warnings == []

    def test_low_confidence_forces_approval(self):
        result = _make_result(confidence=0.3)
        validated = validate_plan(result)

        assert validated.plan.policy_constraints.requires_approval is True
        assert validated.plan.policy_constraints.approval_reason is not None
        assert any("LOW_CONFIDENCE_APPROVAL_REQUIRED" in w for w in validated.plan.warnings)

    def test_high_confidence_no_forced_approval(self):
        result = _make_result(confidence=0.92)
        validated = validate_plan(result)
        assert validated.plan.policy_constraints.requires_approval is False

    def test_no_advance_booking_requirement_skips_check(self):
        result = _make_result(
            policy_constraints=PolicyConstraints(
                max_budget_usd=500.0,
                preferred_vendors=["Delta"],
                advance_booking_days_required=None,
                advance_booking_met=True,
            ),
        )
        validated = validate_plan(result)
        assert validated.plan.warnings == []


# ── Handler tests ───────────────────────────────────────────────────────────


@patch("handlers.validate_plan.validate_plan")
def test_handler_returns_validated_result(mock_validate):
    from handlers.validate_plan import handler

    result = _make_result()
    mock_validate.return_value = result

    output = handler(result.model_dump(mode="json"), None)

    mock_validate.assert_called_once()
    assert output["booking_id"] == "b-1"
    assert output["plan"]["intent"] == "flight_booking"
