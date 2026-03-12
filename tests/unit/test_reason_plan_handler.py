"""Unit tests for the ReasonAndPlan Lambda handler."""

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.errors import ErrorCode, ReasoningError
from core.models.booking import (
    BookingParameters,
    BookingPlan,
    PolicyConstraints,
    PolicySource,
    ReasoningResult,
)

FUTURE = date.today() + timedelta(days=30)
FUTURE2 = date.today() + timedelta(days=37)


def _make_result() -> ReasoningResult:
    plan = BookingPlan(
        intent="flight_booking",
        confidence=0.92,
        parameters=BookingParameters(
            origin="HYD", destination="ORD", departure_date=FUTURE, return_date=FUTURE2, cabin_class="economy"
        ),
        policy_constraints=PolicyConstraints(
            max_budget_usd=500.0,
            preferred_vendors=["Delta", "United"],
            advance_booking_met=True,
        ),
        policy_sources=[PolicySource(chunk_id="c-1", section_title="Air Travel", page=3, similarity_score=0.89)],
        reasoning_summary="Economy, $500 cap.",
    )
    return ReasoningResult(
        booking_id="b-1",
        employee_id="e-1",
        plan=plan,
        model_id="us.amazon.nova-2-lite-v1:0",
        thinking_effort="medium",
        latency_ms=1500.0,
    )


def _make_event() -> dict[str, Any]:
    return {
        "booking_id": "b-1",
        "employee_id": "e-1",
        "user_query": "Book a flight from HYD to ORD",
        "context_text": "Policy: economy only, $500 cap.",
        "confidence_level": "high",
        "max_similarity": 0.89,
    }


@patch("handlers.reason_plan.get_reasoning_service")
@patch("handlers.reason_plan.write_audit_log")
@patch("handlers.reason_plan.get_dynamo_client")
@patch("handlers.reason_plan.get_config")
def test_handler_calls_service_and_returns_result(mock_config, mock_dynamo, mock_audit, mock_svc):
    from handlers.reason_plan import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")
    result = _make_result()
    mock_svc.return_value.generate_booking_plan.return_value = result

    output = handler(_make_event(), None)

    mock_svc.return_value.generate_booking_plan.assert_called_once()
    assert output["booking_id"] == "b-1"
    assert output["plan"]["intent"] == "flight_booking"
    # Dates must be ISO strings for Step Functions
    assert isinstance(output["plan"]["parameters"]["departure_date"], str)


@patch("handlers.reason_plan.get_reasoning_service")
@patch("handlers.reason_plan.write_audit_log")
@patch("handlers.reason_plan.get_dynamo_client")
@patch("handlers.reason_plan.get_config")
def test_handler_writes_audit_log(mock_config, mock_dynamo, mock_audit, mock_svc):
    from handlers.reason_plan import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")
    mock_svc.return_value.generate_booking_plan.return_value = _make_result()

    handler(_make_event(), None)

    mock_audit.assert_called_once()
    call_args = mock_audit.call_args
    assert call_args[0][1] == "AuditLog"  # table name
    entry = call_args[0][2]
    assert entry["event"] == "reasoning_plan"
    assert entry["input"]["model_id"] == "us.amazon.nova-2-lite-v1:0"


@patch("handlers.reason_plan.get_reasoning_service")
@patch("handlers.reason_plan.get_config")
def test_handler_propagates_reasoning_error(mock_config, mock_svc):
    from handlers.reason_plan import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")
    mock_svc.return_value.generate_booking_plan.side_effect = ReasoningError(
        "All 3 attempts failed", code=ErrorCode.REASONING_FAILED
    )

    with pytest.raises(ReasoningError, match="All 3 attempts failed"):
        handler(_make_event(), None)
