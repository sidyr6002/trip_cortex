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
    return {"S": str(obj)}
