"""Lambda handler for embedding a user query and retrieving policy chunks."""

from typing import Any

from core.clients import get_dynamo_client, get_policy_retrieval_service
from core.config import get_config
from core.db.aurora import AuroraClient
from core.models.retrieval import EmbedAndRetrieveRequest, EmbedAndRetrieveResponse
from core.services.audit import build_retrieval_audit_entry, write_audit_log


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    request = EmbedAndRetrieveRequest.model_validate(event)
    service = get_policy_retrieval_service()

    with AuroraClient(config) as aurora_client:
        service._aurora_client = aurora_client
        result = service.retrieve(request.user_query)

    write_audit_log(
        get_dynamo_client(),
        config.audit_log_table,
        build_retrieval_audit_entry(
            booking_id=request.booking_id,
            employee_id=request.employee_id,
            query_length=len(request.user_query),
            total_chunks=result.total_chunks,
            confidence_level=result.confidence.level.value,
            max_similarity=result.confidence.max_similarity,
            action=result.confidence.action,
            latency_ms=result.latency_ms,
        ),
    )

    return EmbedAndRetrieveResponse(
        booking_id=request.booking_id,
        employee_id=request.employee_id,
        user_query=request.user_query,
        context_text=result.context_text,
        confidence=result.confidence,
        total_chunks=result.total_chunks,
        retrieval_latency_ms=result.latency_ms,
    ).model_dump()
