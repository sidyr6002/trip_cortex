"""Unit tests for retrieval Pydantic models."""

import pytest
from pydantic import ValidationError

from core.models.retrieval import QueryEmbeddingRequest, QueryEmbeddingResult, ConfidenceLevel, ConfidenceAssessment, RetrievalResult, PolicyChunkResult, EmbedAndRetrieveRequest, EmbedAndRetrieveResponse


def test_query_embedding_request_valid():
    req = QueryEmbeddingRequest(query_text="fly to NYC", employee_id="emp-123")
    assert req.query_text == "fly to NYC"
    assert req.employee_id == "emp-123"


def test_query_embedding_request_empty_text_rejected():
    with pytest.raises(ValidationError):
        QueryEmbeddingRequest(query_text="", employee_id="emp-123")


def test_query_embedding_request_text_over_limit_rejected():
    with pytest.raises(ValidationError):
        QueryEmbeddingRequest(query_text="x" * 10_001, employee_id="emp-123")


def test_query_embedding_request_text_at_limit_accepted():
    req = QueryEmbeddingRequest(query_text="x" * 10_000, employee_id="emp-123")
    assert len(req.query_text) == 10_000


def test_query_embedding_request_empty_employee_id_rejected():
    with pytest.raises(ValidationError):
        QueryEmbeddingRequest(query_text="fly to NYC", employee_id="")


def test_query_embedding_result_round_trip():
    result = QueryEmbeddingResult(
        embedding=[0.1] * 1024,
        model_id="amazon.nova-2-multimodal-embeddings-v1:0",
        dimension=1024,
        latency_ms=42.5,
    )
    data = result.model_dump()
    restored = QueryEmbeddingResult(**data)
    assert restored == result


def test_confidence_level_serializes_to_string():
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.LOW.value == "low"
    assert ConfidenceLevel.NONE.value == "none"


def test_confidence_assessment_valid():
    ca = ConfidenceAssessment(level=ConfidenceLevel.HIGH, max_similarity=0.89, action="normal")
    assert ca.level == ConfidenceLevel.HIGH
    assert ca.action == "normal"


def test_retrieval_result_round_trip():
    chunk = PolicyChunkResult(
        id="abc", content_text="text", section_title="S1",
        source_page=1, content_type="text", bda_entity_subtype=None, similarity=0.89,
    )
    result = RetrievalResult(
        chunks=[chunk],
        confidence=ConfidenceAssessment(level=ConfidenceLevel.HIGH, max_similarity=0.89, action="normal"),
        context_text="[Section: S1]\ntext",
        total_chunks=1,
        latency_ms=55.0,
    )
    assert RetrievalResult(**result.model_dump()) == result


def test_retrieval_result_empty_chunks_valid():
    result = RetrievalResult(
        chunks=[],
        confidence=ConfidenceAssessment(level=ConfidenceLevel.NONE, max_similarity=0.0, action="apply_strict_defaults"),
        context_text="",
        total_chunks=0,
        latency_ms=10.0,
    )
    assert result.total_chunks == 0
    assert result.context_text == ""


# --- EmbedAndRetrieveRequest ---

def test_embed_and_retrieve_request_valid():
    req = EmbedAndRetrieveRequest(booking_id="b-1", employee_id="emp-1", user_query="book a flight to Chicago")
    assert req.booking_id == "b-1"


def test_embed_and_retrieve_request_empty_user_query_rejected():
    with pytest.raises(ValidationError):
        EmbedAndRetrieveRequest(booking_id="b-1", employee_id="emp-1", user_query="")


def test_embed_and_retrieve_request_user_query_over_limit_rejected():
    with pytest.raises(ValidationError):
        EmbedAndRetrieveRequest(booking_id="b-1", employee_id="emp-1", user_query="x" * 10_001)


def test_embed_and_retrieve_request_empty_booking_id_rejected():
    with pytest.raises(ValidationError):
        EmbedAndRetrieveRequest(booking_id="", employee_id="emp-1", user_query="fly to NYC")


# --- EmbedAndRetrieveResponse ---

def test_embed_and_retrieve_response_confidence_serializes_as_string():
    resp = EmbedAndRetrieveResponse(
        booking_id="b-1",
        employee_id="emp-1",
        user_query="fly to NYC",
        context_text="[Section: Air Travel]\nEconomy only.",
        confidence=ConfidenceAssessment(level=ConfidenceLevel.HIGH, max_similarity=0.89, action="normal"),
        total_chunks=1,
        retrieval_latency_ms=120.5,
    )
    dumped = resp.model_dump()
    assert dumped["confidence"]["level"] == "high"


def test_embed_and_retrieve_response_round_trip():
    resp = EmbedAndRetrieveResponse(
        booking_id="b-1",
        employee_id="emp-1",
        user_query="fly to NYC",
        context_text="",
        confidence=ConfidenceAssessment(level=ConfidenceLevel.NONE, max_similarity=0.0, action="apply_strict_defaults"),
        total_chunks=0,
        retrieval_latency_ms=55.0,
    )
    assert EmbedAndRetrieveResponse(**resp.model_dump()) == resp
