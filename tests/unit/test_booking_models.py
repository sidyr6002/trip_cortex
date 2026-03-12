from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from core.models.booking import BookingParameters, BookingPlan, PolicyConstraints, PolicySource

FUTURE = date.today() + timedelta(days=30)
FUTURE2 = date.today() + timedelta(days=37)


# --- BookingParameters ---


def test_normalizes_origin_destination_to_uppercase():
    p = BookingParameters(origin="hyd", destination="ord", departure_date=FUTURE, cabin_class="economy")
    assert p.origin == "HYD"
    assert p.destination == "ORD"


def test_strips_whitespace_from_airport_codes():
    p = BookingParameters(origin=" JFK ", destination=" LAX ", departure_date=FUTURE, cabin_class="economy")
    assert p.origin == "JFK"
    assert p.destination == "LAX"


def test_rejects_past_departure_date():
    with pytest.raises(ValidationError, match="departure_date must not be in the past"):
        BookingParameters(origin="HYD", destination="ORD", departure_date=date(2020, 1, 1), cabin_class="economy")


def test_normalizes_cabin_class_to_lowercase():
    p = BookingParameters(origin="HYD", destination="ORD", departure_date=FUTURE, cabin_class="Economy")
    assert p.cabin_class == "economy"


def test_normalizes_cabin_class_all_caps():
    p = BookingParameters(origin="HYD", destination="ORD", departure_date=FUTURE, cabin_class="BUSINESS")
    assert p.cabin_class == "business"


def test_rejects_same_origin_and_destination():
    with pytest.raises(ValidationError, match="origin and destination must be different"):
        BookingParameters(origin="HYD", destination="HYD", departure_date=FUTURE, cabin_class="economy")


def test_rejects_return_before_departure():
    with pytest.raises(ValidationError, match="return_date must be after departure_date"):
        BookingParameters(
            origin="HYD",
            destination="ORD",
            departure_date=FUTURE,
            return_date=FUTURE - timedelta(days=1),
            cabin_class="economy",
        )


def test_valid_round_trip():
    p = BookingParameters(
        origin="HYD",
        destination="ORD",
        departure_date=FUTURE,
        return_date=FUTURE2,
        cabin_class="premium_economy",
    )
    assert p.return_date == FUTURE2


def test_passenger_count_bounds():
    with pytest.raises(ValidationError):
        BookingParameters(
            origin="HYD", destination="ORD", departure_date=FUTURE, cabin_class="economy", passenger_count=0
        )
    with pytest.raises(ValidationError):
        BookingParameters(
            origin="HYD", destination="ORD", departure_date=FUTURE, cabin_class="economy", passenger_count=10
        )


# --- PolicyConstraints ---


def _valid_constraints(**overrides) -> dict:
    base = dict(
        max_budget_usd=500.0,
        preferred_vendors=["Delta", "United"],
        advance_booking_days_required=14,
        advance_booking_met=True,
        requires_approval=False,
    )
    base.update(overrides)
    return base


def test_policy_constraints_valid():
    c = PolicyConstraints(**_valid_constraints())
    assert c.max_budget_usd == 500.0


def test_rejects_empty_preferred_vendors():
    with pytest.raises(ValidationError, match="preferred_vendors must contain at least one vendor"):
        PolicyConstraints(**_valid_constraints(preferred_vendors=[]))


def test_rejects_excessive_budget():
    with pytest.raises(ValidationError):
        PolicyConstraints(**_valid_constraints(max_budget_usd=100_000))


def test_rejects_zero_budget():
    with pytest.raises(ValidationError):
        PolicyConstraints(**_valid_constraints(max_budget_usd=0))


def test_requires_approval_reason_when_approval_true():
    with pytest.raises(ValidationError, match="approval_reason is required"):
        PolicyConstraints(**_valid_constraints(requires_approval=True, approval_reason=None))


def test_approval_reason_not_required_when_approval_false():
    c = PolicyConstraints(**_valid_constraints(requires_approval=False, approval_reason=None))
    assert c.approval_reason is None


# --- BookingPlan ---


def _valid_plan(**overrides) -> dict:
    base = dict(
        intent="flight_booking",
        confidence=0.95,
        parameters=BookingParameters(origin="HYD", destination="ORD", departure_date=FUTURE, cabin_class="economy"),
        policy_constraints=PolicyConstraints(**_valid_constraints()),
        policy_sources=[PolicySource(chunk_id="abc", section_title="Air Travel", page=1, similarity_score=0.9)],
        reasoning_summary="Test plan",
    )
    base.update(overrides)
    return base


def test_booking_plan_valid():
    plan = BookingPlan(**_valid_plan())
    assert plan.intent == "flight_booking"
    assert plan.warnings == []


def test_booking_plan_rejects_invalid_intent():
    with pytest.raises(ValidationError):
        BookingPlan(**_valid_plan(intent="hotel_booking"))


def test_booking_plan_confidence_upper_bound():
    with pytest.raises(ValidationError):
        BookingPlan(**_valid_plan(confidence=1.5))


def test_booking_plan_confidence_lower_bound():
    with pytest.raises(ValidationError):
        BookingPlan(**_valid_plan(confidence=-0.1))


def test_strict_defaults_returns_valid_plan():
    plan = BookingPlan.strict_defaults("hyd", "ord", FUTURE)
    assert plan.confidence == 0.0
    assert plan.parameters.origin == "HYD"
    assert plan.parameters.destination == "ORD"
    assert plan.parameters.cabin_class == "economy"
    assert plan.policy_constraints.max_budget_usd == 300.0
    assert plan.policy_constraints.requires_approval is True
    assert plan.policy_constraints.approval_reason is not None
    assert "STRICT_DEFAULTS_APPLIED" in plan.warnings


def test_strict_defaults_with_return_date():
    plan = BookingPlan.strict_defaults("HYD", "ORD", FUTURE, return_date=FUTURE2)
    assert plan.parameters.return_date == FUTURE2


# --- ReasoningRequest ---

from core.models.booking import ReasoningRequest, ReasoningResult  # noqa: E402


def test_reasoning_request_valid():
    r = ReasoningRequest(
        booking_id="b-1",
        employee_id="e-1",
        user_query="Book a flight from HYD to ORD",
        context_text="Policy: economy only, $500 cap",
        confidence_level="high",
        max_similarity=0.92,
    )
    assert r.confidence_level == "high"


def test_reasoning_request_rejects_empty_booking_id():
    with pytest.raises(ValidationError):
        ReasoningRequest(
            booking_id="",
            employee_id="e-1",
            user_query="fly me",
            context_text="policy",
            confidence_level="high",
            max_similarity=0.9,
        )


def test_reasoning_request_rejects_long_query():
    with pytest.raises(ValidationError):
        ReasoningRequest(
            booking_id="b-1",
            employee_id="e-1",
            user_query="x" * 10_001,
            context_text="policy",
            confidence_level="low",
            max_similarity=0.5,
        )


def test_reasoning_request_confidence_levels():
    for level in ("high", "low", "none"):
        r = ReasoningRequest(
            booking_id="b-1",
            employee_id="e-1",
            user_query="fly",
            context_text="policy",
            confidence_level=level,
            max_similarity=0.5,
        )
        assert r.confidence_level == level

    with pytest.raises(ValidationError):
        ReasoningRequest(
            booking_id="b-1",
            employee_id="e-1",
            user_query="fly",
            context_text="policy",
            confidence_level="unknown",
            max_similarity=0.5,
        )


# --- ReasoningResult ---


def _make_plan() -> BookingPlan:
    return BookingPlan(**_valid_plan())


def test_reasoning_result_valid():
    result = ReasoningResult(
        booking_id="b-1",
        employee_id="e-1",
        plan=_make_plan(),
        model_id="us.amazon.nova-2-lite-v1:0",
        thinking_effort="medium",
        latency_ms=1234.5,
    )
    assert result.retry_count == 0
    assert result.escalated is False


def test_reasoning_result_thinking_effort_values():
    for effort in ("low", "medium", "high"):
        r = ReasoningResult(
            booking_id="b-1",
            employee_id="e-1",
            plan=_make_plan(),
            model_id="us.amazon.nova-2-lite-v1:0",
            thinking_effort=effort,
            latency_ms=100.0,
        )
        assert r.thinking_effort == effort

    with pytest.raises(ValidationError):
        ReasoningResult(
            booking_id="b-1",
            employee_id="e-1",
            plan=_make_plan(),
            model_id="us.amazon.nova-2-lite-v1:0",
            thinking_effort="extreme",
            latency_ms=100.0,
        )


def test_reasoning_result_model_dump_is_json_serializable():
    import json

    result = ReasoningResult(
        booking_id="b-1",
        employee_id="e-1",
        plan=_make_plan(),
        model_id="us.amazon.nova-2-lite-v1:0",
        thinking_effort="high",
        latency_ms=500.0,
        retry_count=1,
        escalated=True,
    )
    dumped = result.model_dump(mode="json")
    # Must not raise
    json.dumps(dumped)
    # date fields must be strings
    assert isinstance(dumped["plan"]["parameters"]["departure_date"], str)
