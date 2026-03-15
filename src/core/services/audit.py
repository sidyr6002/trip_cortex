"""Audit log helper — writes decision records to DynamoDB AuditLogTable."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog

logger = structlog.get_logger()


def write_audit_log(dynamo_client: Any, table_name: str, entry: dict[str, Any]) -> None:
    """Write an audit entry to DynamoDB. Swallows exceptions — audit failure must not block the workflow."""
    try:
        item = {k: _to_dynamo(v) for k, v in entry.items()}
        dynamo_client.put_item(TableName=table_name, Item=item)
    except Exception:
        logger.error("audit_log_write_failed", table=table_name, exc_info=True)


def build_retrieval_audit_entry(
    booking_id: str,
    employee_id: str,
    query_length: int,
    total_chunks: int,
    confidence_level: str,
    max_similarity: float,
    action: str,
    latency_ms: float,
) -> dict[str, Any]:
    return {
        "auditId": str(uuid4()),
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "policy_retrieval",
        "input": {"query_length": query_length, "content_type_filter": None},
        "output": {
            "total_chunks": total_chunks,
            "confidence_level": confidence_level,
            "max_similarity": max_similarity,
            "action": action,
        },
        "latency_ms": latency_ms,
    }


def build_reasoning_audit_entry(
    booking_id: str,
    employee_id: str,
    model_id: str,
    thinking_effort: str,
    latency_ms: float,
    retry_count: int,
    escalated: bool,
    plan_confidence: float,
    plan_intent: str,
    warnings_count: int,
) -> dict[str, Any]:
    return {
        "auditId": str(uuid4()),
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "reasoning_plan",
        "input": {
            "model_id": model_id,
            "thinking_effort": thinking_effort,
            "escalated": escalated,
        },
        "output": {
            "plan_confidence": plan_confidence,
            "plan_intent": plan_intent,
            "retry_count": retry_count,
            "warnings_count": warnings_count,
        },
        "latency_ms": latency_ms,
    }


def build_flight_search_audit_entry(
    booking_id: str,
    employee_id: str,
    total_results: int,
    flights_returned: int,
    fallback_url_set: bool,
    warnings: list[str],
    latency_ms: float,
    total_attempts: int = 1,
    recovery_strategies_used: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "auditId": f"flight-search-{uuid4()}",
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "flight_search",
        "output": {
            "total_results": total_results,
            "flights_returned": flights_returned,
            "fallback_url_set": fallback_url_set,
            "warnings": warnings,
            "total_attempts": total_attempts,
            "recovery_strategies_used": recovery_strategies_used or [],
        },
        "latency_ms": latency_ms,
    }


def build_recovery_audit_entry(
    booking_id: str,
    employee_id: str,
    attempt: int,
    strategy: str,
    error_type: str,
    success: bool,
    latency_ms: float,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "auditId": f"recovery-{uuid4()}",
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "recovery_attempt",
        "input": {"attempt": attempt, "strategy": strategy, "error_type": error_type},
        "output": {"success": success},
        "latency_ms": latency_ms,
        "ttl": int(now.timestamp()) + 90 * 86400,
    }


def build_degradation_audit_entry(
    booking_id: str,
    employee_id: str,
    error_code: str,
    original_error_message: str,
) -> dict[str, Any]:
    return {
        "auditId": str(uuid4()),
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "graceful_degradation",
        "input": {
            "error_code": error_code,
            "original_error_message": original_error_message[:200],
        },
        "output": {
            "plan_confidence": 0.0,
            "warnings": ["STRICT_DEFAULTS_APPLIED"],
        },
    }


def _to_dynamo(obj: Any) -> Any:
    """Recursively convert a Python value to DynamoDB attribute format."""
    if isinstance(obj, dict):
        return {"M": {k: _to_dynamo(v) for k, v in obj.items()}}
    if isinstance(obj, str):
        return {"S": obj}
    if isinstance(obj, bool):
        return {"BOOL": obj}
    if isinstance(obj, (int, float)):
        return {"N": str(obj)}
    if obj is None:
        return {"NULL": True}
    if isinstance(obj, list):
        return {"L": [_to_dynamo(item) for item in obj]}
    return {"S": str(obj)}
