"""Unit tests for retrieval Pydantic models."""

import pytest
from pydantic import ValidationError

from core.models.retrieval import QueryEmbeddingRequest, QueryEmbeddingResult


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
