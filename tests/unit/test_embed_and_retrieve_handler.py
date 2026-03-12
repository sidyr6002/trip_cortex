"""Unit tests for embed_and_retrieve handler."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from core.models.retrieval import ConfidenceAssessment, ConfidenceLevel, PolicyChunkResult, RetrievalResult


@pytest.fixture
def mock_result():
    return RetrievalResult(
        chunks=[
            PolicyChunkResult(
                id="c-1", content_text="Economy only.", section_title="Air Travel",
                source_page=3, content_type="text", bda_entity_subtype=None, similarity=0.89,
            )
        ],
        confidence=ConfidenceAssessment(level=ConfidenceLevel.HIGH, max_similarity=0.89, action="normal"),
        context_text="[Section: Air Travel | Page: 3 | Type: text | Similarity: 0.89]\nEconomy only.",
        total_chunks=1,
        latency_ms=120.5,
    )


@pytest.fixture
def valid_event():
    return {"booking_id": "b-1", "employee_id": "emp-1", "user_query": "book a flight to Chicago"}


def _call_handler(valid_event, mock_result):
    with (
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
        patch("handlers.embed_and_retrieve.get_policy_retrieval_service") as mock_factory,
        patch("handlers.embed_and_retrieve.AuroraClient") as mock_aurora_cls,
        patch("handlers.embed_and_retrieve.get_dynamo_client") as mock_dynamo,
        patch("handlers.embed_and_retrieve.write_audit_log"),
    ):
        mock_cfg.return_value = MagicMock(audit_log_table="AuditLogTable")
        mock_service = MagicMock()
        mock_service.retrieve.return_value = mock_result
        mock_factory.return_value = mock_service
        mock_aurora_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_aurora_cls.return_value.__exit__ = MagicMock(return_value=False)

        from handlers.embed_and_retrieve import handler
        return handler(valid_event, None), mock_service, mock_aurora_cls, mock_dynamo


def test_handler_returns_all_required_fields(valid_event, mock_result):
    response, *_ = _call_handler(valid_event, mock_result)
    assert response["booking_id"] == "b-1"
    assert response["employee_id"] == "emp-1"
    assert response["user_query"] == "book a flight to Chicago"
    assert response["context_text"] == mock_result.context_text
    assert response["total_chunks"] == 1
    assert response["retrieval_latency_ms"] == 120.5


def test_handler_confidence_serialized_as_string(valid_event, mock_result):
    response, *_ = _call_handler(valid_event, mock_result)
    assert response["confidence"]["level"] == "high"


def test_handler_booking_and_employee_id_pass_through(valid_event, mock_result):
    response, *_ = _call_handler(valid_event, mock_result)
    assert response["booking_id"] == valid_event["booking_id"]
    assert response["employee_id"] == valid_event["employee_id"]


def test_handler_missing_booking_id_raises_validation_error():
    from handlers.embed_and_retrieve import handler
    with pytest.raises(ValidationError):
        handler({"employee_id": "emp-1", "user_query": "fly to NYC"}, None)


def test_handler_missing_user_query_raises_validation_error():
    from handlers.embed_and_retrieve import handler
    with pytest.raises(ValidationError):
        handler({"booking_id": "b-1", "employee_id": "emp-1"}, None)


def test_handler_retrieval_error_propagates(valid_event, mock_result):
    from core.errors import ErrorCode, PolicyRetrievalError
    with (
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
        patch("handlers.embed_and_retrieve.get_policy_retrieval_service") as mock_factory,
        patch("handlers.embed_and_retrieve.AuroraClient") as mock_aurora_cls,
        patch("handlers.embed_and_retrieve.get_dynamo_client"),
    ):
        mock_cfg.return_value = MagicMock(audit_log_table="AuditLogTable")
        mock_service = MagicMock()
        mock_service.retrieve.side_effect = PolicyRetrievalError("search failed", code=ErrorCode.RETRIEVAL_FAILED)
        mock_factory.return_value = mock_service
        mock_aurora_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_aurora_cls.return_value.__exit__ = MagicMock(return_value=False)

        from handlers.embed_and_retrieve import handler
        with pytest.raises(PolicyRetrievalError):
            handler(valid_event, None)


def test_handler_aurora_disconnect_called_on_success(valid_event, mock_result):
    _, _, mock_aurora_cls, _ = _call_handler(valid_event, mock_result)
    mock_aurora_cls.return_value.__exit__.assert_called_once()


def test_handler_write_audit_log_called_once(valid_event, mock_result):
    with (
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
        patch("handlers.embed_and_retrieve.get_policy_retrieval_service") as mock_factory,
        patch("handlers.embed_and_retrieve.AuroraClient") as mock_aurora_cls,
        patch("handlers.embed_and_retrieve.get_dynamo_client"),
        patch("handlers.embed_and_retrieve.write_audit_log") as mock_audit,
    ):
        mock_cfg.return_value = MagicMock(audit_log_table="AuditLogTable")
        mock_service = MagicMock()
        mock_service.retrieve.return_value = mock_result
        mock_factory.return_value = mock_service
        mock_aurora_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_aurora_cls.return_value.__exit__ = MagicMock(return_value=False)

        from handlers.embed_and_retrieve import handler
        handler(valid_event, None)
        mock_audit.assert_called_once()


def test_handler_audit_failure_does_not_prevent_response(valid_event, mock_result):
    with (
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
        patch("handlers.embed_and_retrieve.get_policy_retrieval_service") as mock_factory,
        patch("handlers.embed_and_retrieve.AuroraClient") as mock_aurora_cls,
        patch("handlers.embed_and_retrieve.get_dynamo_client"),
        patch("handlers.embed_and_retrieve.write_audit_log", side_effect=Exception("dynamo down")),
    ):
        mock_cfg.return_value = MagicMock(audit_log_table="AuditLogTable")
        mock_service = MagicMock()
        mock_service.retrieve.return_value = mock_result
        mock_factory.return_value = mock_service
        mock_aurora_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_aurora_cls.return_value.__exit__ = MagicMock(return_value=False)

        from handlers.embed_and_retrieve import handler
        # write_audit_log itself swallows exceptions internally, but even if it raises here,
        # the test verifies the contract: audit failure should not surface to the caller.
        # Since write_audit_log is patched to raise, this test documents that the handler
        # does NOT catch it — the swallowing happens inside write_audit_log itself (Task 2).
        # So we just verify the real write_audit_log swallows — call with real impl:

    # Re-run with real write_audit_log but failing dynamo
    with (
        patch("handlers.embed_and_retrieve.get_config") as mock_cfg,
        patch("handlers.embed_and_retrieve.get_policy_retrieval_service") as mock_factory,
        patch("handlers.embed_and_retrieve.AuroraClient") as mock_aurora_cls,
        patch("handlers.embed_and_retrieve.get_dynamo_client") as mock_dynamo,
    ):
        mock_cfg.return_value = MagicMock(audit_log_table="AuditLogTable")
        mock_service = MagicMock()
        mock_service.retrieve.return_value = mock_result
        mock_factory.return_value = mock_service
        mock_aurora_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_aurora_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_dynamo.return_value.put_item.side_effect = Exception("dynamo down")

        from handlers.embed_and_retrieve import handler
        response = handler(valid_event, None)
        assert response["booking_id"] == "b-1"
