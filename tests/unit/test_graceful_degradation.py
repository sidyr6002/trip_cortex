"""Unit tests for graceful degradation service, audit entry, and handler."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from core.models.booking import ReasoningResult
from core.services.audit import build_degradation_audit_entry
from core.services.graceful_degradation import apply_graceful_degradation


# ── apply_graceful_degradation ───────────────────────────────────────────────


def test_returns_valid_reasoning_result():
    result = apply_graceful_degradation("b-1", "e-1")
    assert isinstance(result, ReasoningResult)
    assert result.plan.confidence == 0.0
    assert result.plan.policy_constraints.requires_approval is True
    assert "STRICT_DEFAULTS_APPLIED" in result.plan.warnings


def test_uses_economy_300_cap():
    result = apply_graceful_degradation("b-1", "e-1")
    assert result.plan.parameters.cabin_class == "economy"
    assert result.plan.policy_constraints.max_budget_usd == 300.0
    assert result.plan.policy_constraints.advance_booking_days_required == 14


def test_model_id_sentinel():
    result = apply_graceful_degradation("b-1", "e-1")
    assert result.model_id == "strict-defaults"


def test_placeholder_airports_are_distinct():
    result = apply_graceful_degradation("b-1", "e-1")
    assert result.plan.parameters.origin != result.plan.parameters.destination


def test_output_matches_reasoning_result_schema():
    result = apply_graceful_degradation("b-1", "e-1")
    dumped = result.model_dump(mode="json")
    serialized = json.dumps(dumped)
    reparsed = ReasoningResult.model_validate(json.loads(serialized))
    assert reparsed.booking_id == "b-1"


# ── build_degradation_audit_entry ────────────────────────────────────────────


@pytest.fixture
def degradation_entry() -> dict[str, Any]:
    return build_degradation_audit_entry(
        booking_id="b-1",
        employee_id="e-1",
        error_code="ReasoningError",
        original_error_message="All 3 attempts failed",
    )


def test_audit_entry_event_type(degradation_entry):
    assert degradation_entry["event"] == "graceful_degradation"


def test_audit_entry_output_fields(degradation_entry):
    assert degradation_entry["output"]["plan_confidence"] == 0.0
    assert degradation_entry["output"]["warnings"] == ["STRICT_DEFAULTS_APPLIED"]


def test_audit_entry_no_pii(degradation_entry):
    serialized = json.dumps(degradation_entry)
    for forbidden in ("user_query", "cabin_class", "departure_date", "\"origin\"", "\"destination\""):
        assert forbidden not in serialized


def test_audit_entry_truncates_long_error():
    long_msg = "x" * 300
    entry = build_degradation_audit_entry("b-1", "e-1", "ReasoningError", long_msg)
    assert len(entry["input"]["original_error_message"]) == 200


def test_audit_entry_short_error_not_truncated():
    entry = build_degradation_audit_entry("b-1", "e-1", "ReasoningError", "short error")
    assert entry["input"]["original_error_message"] == "short error"


# ── graceful_degradation handler ─────────────────────────────────────────────


def _make_event() -> dict[str, Any]:
    return {
        "booking_id": "b-1",
        "employee_id": "e-1",
        "user_query": "Book a flight from HYD to ORD",
        "error": "ReasoningError",
        "cause": "All 3 attempts failed",
    }


@patch("handlers.graceful_degradation.write_audit_log")
@patch("handlers.graceful_degradation.get_dynamo_client")
@patch("handlers.graceful_degradation.get_config")
def test_handler_calls_service_and_writes_audit(mock_config, mock_dynamo, mock_audit):
    from handlers.graceful_degradation import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")

    output = handler(_make_event(), None)

    mock_audit.assert_called_once()
    entry = mock_audit.call_args[0][2]
    assert entry["event"] == "graceful_degradation"
    assert output["plan"]["confidence"] == 0.0
    assert "STRICT_DEFAULTS_APPLIED" in output["plan"]["warnings"]


@patch("handlers.graceful_degradation.write_audit_log")
@patch("handlers.graceful_degradation.get_dynamo_client")
@patch("handlers.graceful_degradation.get_config")
def test_handler_output_consumable_by_validate_plan(mock_config, mock_dynamo, mock_audit):
    from handlers.graceful_degradation import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")
    output = handler(_make_event(), None)

    reparsed = ReasoningResult.model_validate(output)
    assert reparsed.plan.policy_constraints.requires_approval is True


@patch("handlers.graceful_degradation.write_audit_log")
@patch("handlers.graceful_degradation.get_dynamo_client")
@patch("handlers.graceful_degradation.get_config")
def test_handler_tolerates_missing_error_fields(mock_config, mock_dynamo, mock_audit):
    from handlers.graceful_degradation import handler

    mock_config.return_value = MagicMock(audit_log_table="AuditLog")
    event = {"booking_id": "b-1", "employee_id": "e-1"}

    output = handler(event, None)
    assert output["booking_id"] == "b-1"
