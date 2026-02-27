from datetime import date

import pytest
from pydantic import ValidationError

from core.models import BookingParameters, BookingPlan, PolicyConstraints, PolicySource

VALID_PARAMS = dict(
    origin="HYD",
    destination="ORD",
    departure_date=date(2026, 3, 10),
    return_date=date(2026, 3, 12),
    cabin_class="economy",
    time_preference="morning",
    passenger_count=1,
)

VALID_CONSTRAINTS = dict(
    max_budget_usd=500.0,
    preferred_vendors=["Delta", "United"],
    advance_booking_days_required=14,
    advance_booking_met=True,
    requires_approval=False,
    approval_reason=None,
)

VALID_SOURCE = dict(chunk_id="uuid-here", section_title="Domestic Air Travel Policy", page=3, similarity_score=0.89)

VALID_PLAN_JSON = {
    "intent": "flight_booking",
    "confidence": 0.95,
    "parameters": VALID_PARAMS,
    "policy_constraints": VALID_CONSTRAINTS,
    "policy_sources": [VALID_SOURCE],
    "reasoning_summary": "Employee requests HYD→ORD round trip.",
    "warnings": [],
    "fallback_url": None,
}


# --- BookingParameters ---


def test_booking_parameters_valid():
    p = BookingParameters(**VALID_PARAMS)
    assert p.model_dump()["origin"] == "HYD"


def test_booking_parameters_origin_too_short():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "origin": "HY"})


def test_booking_parameters_origin_too_long():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "origin": "HYDDD"})


def test_booking_parameters_invalid_cabin_class():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "cabin_class": "luxury"})


def test_booking_parameters_return_before_departure():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "return_date": date(2026, 3, 9)})


def test_booking_parameters_passenger_count_zero():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "passenger_count": 0})


def test_booking_parameters_passenger_count_too_high():
    with pytest.raises(ValidationError):
        BookingParameters(**{**VALID_PARAMS, "passenger_count": 10})


# --- PolicyConstraints ---


def test_policy_constraints_valid():
    c = PolicyConstraints(**VALID_CONSTRAINTS)
    assert c.max_budget_usd == 500.0


def test_policy_constraints_budget_zero():
    with pytest.raises(ValidationError):
        PolicyConstraints(**{**VALID_CONSTRAINTS, "max_budget_usd": 0})


def test_policy_constraints_budget_negative():
    with pytest.raises(ValidationError):
        PolicyConstraints(**{**VALID_CONSTRAINTS, "max_budget_usd": -100})


# --- PolicySource ---


def test_policy_source_valid():
    s = PolicySource(**VALID_SOURCE)
    assert s.similarity_score == 0.89


def test_policy_source_score_too_high():
    with pytest.raises(ValidationError):
        PolicySource(**{**VALID_SOURCE, "similarity_score": 1.5})


def test_policy_source_score_negative():
    with pytest.raises(ValidationError):
        PolicySource(**{**VALID_SOURCE, "similarity_score": -0.1})


# --- BookingPlan ---


def test_booking_plan_valid_from_json():
    plan = BookingPlan.model_validate(VALID_PLAN_JSON)
    assert plan.intent == "flight_booking"
    assert plan.confidence == 0.95
    assert plan.policy_sources[0].chunk_id == "uuid-here"


def test_booking_plan_invalid_intent():
    with pytest.raises(ValidationError):
        BookingPlan.model_validate({**VALID_PLAN_JSON, "intent": "hotel_booking"})


def test_booking_plan_confidence_too_high():
    with pytest.raises(ValidationError):
        BookingPlan.model_validate({**VALID_PLAN_JSON, "confidence": 1.5})
