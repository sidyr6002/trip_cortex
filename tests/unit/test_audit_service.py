"""Unit tests for audit log helper."""

from unittest.mock import MagicMock, patch

import pytest

from core.services.audit import build_reasoning_audit_entry, build_retrieval_audit_entry, write_audit_log


@pytest.fixture
def dynamo():
    return MagicMock()


@pytest.fixture
def entry():
    return build_retrieval_audit_entry(
        booking_id="b-1",
        employee_id="emp-1",
        query_length=42,
        total_chunks=3,
        confidence_level="high",
        max_similarity=0.89,
        action="normal",
        latency_ms=120.5,
    )


def test_write_audit_log_calls_put_item(dynamo, entry):
    write_audit_log(dynamo, "AuditLogTable", entry)
    dynamo.put_item.assert_called_once()
    call_kwargs = dynamo.put_item.call_args[1]
    assert call_kwargs["TableName"] == "AuditLogTable"


def test_write_audit_log_swallows_exception(dynamo, entry):
    dynamo.put_item.side_effect = Exception("DynamoDB unavailable")
    write_audit_log(dynamo, "AuditLogTable", entry)  # must not raise


def test_write_audit_log_emits_structlog_error_on_failure(dynamo, entry):
    dynamo.put_item.side_effect = Exception("timeout")
    with patch("core.services.audit.logger") as mock_logger:
        write_audit_log(dynamo, "AuditLogTable", entry)
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args[0][0] == "audit_log_write_failed"


def test_build_retrieval_audit_entry_structure(entry):
    assert entry["event"] == "policy_retrieval"
    assert entry["bookingId"] == "b-1"
    assert entry["employeeId"] == "emp-1"


def test_build_retrieval_audit_entry_no_query_text(entry):
    # user_query must never appear in the audit record
    import json

    serialized = json.dumps(entry)
    assert "user_query" not in serialized
    assert "query_text" not in serialized


def test_build_retrieval_audit_entry_audit_id_is_uuid(entry):
    import re

    assert re.match(r"^[0-9a-f-]{36}$", entry["auditId"])


def test_build_retrieval_audit_entry_timestamp_is_utc_iso(entry):
    ts = entry["timestamp"]
    assert ts.endswith("Z")
    assert "T" in ts


def test_build_retrieval_audit_entry_output_fields(entry):
    out = entry["output"]
    assert out["total_chunks"] == 3
    assert out["confidence_level"] == "high"
    assert out["max_similarity"] == 0.89
    assert out["action"] == "normal"


def test_dynamo_item_strings_use_s_type(dynamo, entry):
    write_audit_log(dynamo, "AuditLogTable", entry)
    item = dynamo.put_item.call_args[1]["Item"]
    assert item["bookingId"] == {"S": "b-1"}
    assert item["employeeId"] == {"S": "emp-1"}
    assert item["event"] == {"S": "policy_retrieval"}


def test_dynamo_item_numbers_use_n_type(dynamo, entry):
    write_audit_log(dynamo, "AuditLogTable", entry)
    item = dynamo.put_item.call_args[1]["Item"]
    assert item["latency_ms"] == {"N": "120.5"}


def test_dynamo_item_nested_dict_uses_m_type(dynamo, entry):
    write_audit_log(dynamo, "AuditLogTable", entry)
    item = dynamo.put_item.call_args[1]["Item"]
    assert "M" in item["output"]
    assert item["output"]["M"]["confidence_level"] == {"S": "high"}


# ── build_reasoning_audit_entry ─────────────────────────────────────────────


@pytest.fixture
def reasoning_entry():
    return build_reasoning_audit_entry(
        booking_id="b-2",
        employee_id="emp-2",
        model_id="us.amazon.nova-2-lite-v1:0",
        thinking_effort="high",
        latency_ms=3200.5,
        retry_count=2,
        escalated=True,
        plan_confidence=0.92,
        plan_intent="flight_booking",
        warnings_count=0,
    )


def test_reasoning_audit_entry_structure(reasoning_entry):
    assert reasoning_entry["event"] == "reasoning_plan"
    assert reasoning_entry["bookingId"] == "b-2"
    assert reasoning_entry["employeeId"] == "emp-2"
    assert reasoning_entry["latency_ms"] == 3200.5

    inp = reasoning_entry["input"]
    assert inp["model_id"] == "us.amazon.nova-2-lite-v1:0"
    assert inp["thinking_effort"] == "high"
    assert inp["escalated"] is True

    out = reasoning_entry["output"]
    assert out["plan_confidence"] == 0.92
    assert out["plan_intent"] == "flight_booking"
    assert out["retry_count"] == 2
    assert out["warnings_count"] == 0


def test_reasoning_audit_entry_no_pii(reasoning_entry):
    import json

    serialized = json.dumps(reasoning_entry)
    for forbidden in ("user_query", "query_text", "origin", "destination", "plan_parameters"):
        assert forbidden not in serialized
