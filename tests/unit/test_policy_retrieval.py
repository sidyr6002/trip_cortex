"""Unit tests for PolicyRetrievalService."""

from unittest.mock import MagicMock, patch

import pytest

from core.errors import PolicyRetrievalError, ValidationError
from core.models.retrieval import ConfidenceLevel, PolicyChunkResult
from core.services.policy_retrieval import PolicyRetrievalService


def _make_chunk(section: str, page: int, content_type: str, similarity: float) -> PolicyChunkResult:
    return PolicyChunkResult(
        id="id",
        content_text=f"content of {section}",
        section_title=section,
        source_page=page,
        content_type=content_type,
        bda_entity_subtype=None,
        similarity=similarity,
    )


def _make_config(similarity_threshold=0.65, high_confidence_threshold=0.75, retrieval_top_k=5, hnsw_ef_search=40):
    cfg = MagicMock()
    cfg.similarity_threshold = similarity_threshold
    cfg.high_confidence_threshold = high_confidence_threshold
    cfg.retrieval_top_k = retrieval_top_k
    cfg.hnsw_ef_search = hnsw_ef_search
    return cfg


@pytest.fixture
def chunks():
    return [
        _make_chunk("Domestic Air Travel", 3, "text", 0.89),
        _make_chunk("Expense Limits", 7, "table", 0.72),
        _make_chunk("Booking Deadlines", 5, "text", 0.68),
    ]


@pytest.fixture
def service(chunks):
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = chunks
    return PolicyRetrievalService(embed_svc, aurora, _make_config())


def test_retrieve_returns_high_confidence(service, chunks):
    result = service.retrieve("book a flight to Chicago")
    assert result.confidence.level == ConfidenceLevel.HIGH
    assert result.confidence.max_similarity == 0.89
    assert result.confidence.action == "normal"
    assert result.total_chunks == 3
    assert result.latency_ms > 0


def test_retrieve_no_chunks_returns_none_confidence():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = []
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config())

    result = svc.retrieve("book a flight")
    assert result.confidence.level == ConfidenceLevel.NONE
    assert result.confidence.action == "apply_strict_defaults"
    assert result.context_text == ""
    assert result.total_chunks == 0


def test_retrieve_low_confidence():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = [_make_chunk("S", 1, "text", 0.70)]
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config())

    result = svc.retrieve("book a flight")
    assert result.confidence.level == ConfidenceLevel.LOW
    assert result.confidence.action == "flag_low_confidence"


def test_retrieve_boundary_exactly_at_high_threshold_is_low():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = [_make_chunk("S", 1, "text", 0.75)]
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config())

    result = svc.retrieve("book a flight")
    assert result.confidence.level == ConfidenceLevel.LOW  # > 0.75 required for HIGH


def test_retrieve_passes_content_type_filter(service):
    service.retrieve("book a flight", content_type="text")
    service._aurora_client.similarity_search.assert_called_once_with(
        query_embedding=[0.1] * 1024,
        threshold=0.65,
        top_k=5,
        ef_search=40,
        content_type="text",
    )


def test_assemble_context_formats_chunks(service, chunks):
    result = service.retrieve("book a flight")
    assert "[Section: Domestic Air Travel | Page: 3 | Type: text | Similarity: 0.89]" in result.context_text
    assert "[Section: Expense Limits | Page: 7 | Type: table | Similarity: 0.72]" in result.context_text
    assert "[Section: Booking Deadlines | Page: 5 | Type: text | Similarity: 0.68]" in result.context_text
    assert "content of Domestic Air Travel" in result.context_text
    assert result.context_text.count("---") == 2  # 3 chunks → 2 separators


def test_assemble_context_empty_returns_empty_string():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = []
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config())
    assert svc._assemble_context([]) == ""


def test_embedding_failure_propagates():
    embed_svc = MagicMock()
    embed_svc.embed_query.side_effect = PolicyRetrievalError("bedrock down")
    svc = PolicyRetrievalService(embed_svc, MagicMock(), _make_config())
    with pytest.raises(PolicyRetrievalError):
        svc.retrieve("book a flight")


def test_aurora_failure_propagates():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.side_effect = PolicyRetrievalError("db down")
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config())
    with pytest.raises(PolicyRetrievalError):
        svc.retrieve("book a flight")


def test_validation_error_propagates():
    embed_svc = MagicMock()
    embed_svc.embed_query.side_effect = ValidationError("empty query")
    svc = PolicyRetrievalService(embed_svc, MagicMock(), _make_config())
    with pytest.raises(ValidationError):
        svc.retrieve("")


def test_structlog_emits_policy_retrieved_without_query_text(service):
    with patch("core.services.policy_retrieval.logger") as mock_logger:
        service.retrieve("book a flight to Chicago")
    mock_logger.info.assert_called_once()
    _, kwargs = mock_logger.info.call_args
    assert kwargs["results_count"] == 3
    assert kwargs["confidence_level"] == "high"
    assert kwargs["max_similarity"] == 0.89
    assert kwargs["action"] == "normal"
    assert "query_text" not in kwargs
    assert "latency_ms" in kwargs


def test_custom_thresholds_change_confidence_classification():
    embed_svc = MagicMock()
    embed_svc.embed_query.return_value = [0.1] * 1024
    aurora = MagicMock()
    aurora.similarity_search.return_value = [_make_chunk("S", 1, "text", 0.89)]
    # With high_confidence_threshold=0.90, similarity 0.89 should be LOW
    svc = PolicyRetrievalService(embed_svc, aurora, _make_config(high_confidence_threshold=0.90))

    result = svc.retrieve("book a flight")
    assert result.confidence.level == ConfidenceLevel.LOW
