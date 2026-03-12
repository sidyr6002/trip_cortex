"""Unit tests for QueryEmbeddingService."""

import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from core.errors import PolicyRetrievalError, ValidationError
from core.services.query_embedding import QueryEmbeddingService

_VECTOR = [0.1] * 1024
_MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.invoke_model.return_value = {
        "body": MagicMock(read=lambda: json.dumps({"embeddings": [{"embedding": _VECTOR}]}).encode())
    }
    return client


@pytest.fixture
def service(mock_client):
    return QueryEmbeddingService(mock_client, _MODEL_ID)


def test_embed_query_returns_vector(service):
    result = service.embed_query("book a flight to Chicago")
    assert result == _VECTOR
    assert len(result) == 1024


def test_embed_query_uses_generic_retrieval_purpose(service, mock_client):
    service.embed_query("book a flight to Chicago")
    body = json.loads(mock_client.invoke_model.call_args.kwargs["body"])
    assert body["singleEmbeddingParams"]["embeddingPurpose"] == "GENERIC_RETRIEVAL"


def test_embed_query_not_generic_index(service, mock_client):
    service.embed_query("book a flight to Chicago")
    body = json.loads(mock_client.invoke_model.call_args.kwargs["body"])
    assert body["singleEmbeddingParams"]["embeddingPurpose"] != "GENERIC_INDEX"


def test_empty_text_raises_validation_error(service):
    with pytest.raises(ValidationError):
        service.embed_query("")


def test_text_over_limit_raises_validation_error(service):
    with pytest.raises(ValidationError):
        service.embed_query("x" * 10_001)


def test_text_at_limit_is_accepted(service):
    result = service.embed_query("x" * 10_000)
    assert result == _VECTOR


def test_bedrock_failure_propagates_as_policy_retrieval_error(mock_client):
    error = ClientError({"Error": {"Code": "ValidationException", "Message": ""}}, "InvokeModel")
    mock_client.invoke_model.side_effect = error
    svc = QueryEmbeddingService(mock_client, _MODEL_ID)
    with pytest.raises(PolicyRetrievalError):
        svc.embed_query("book a flight")
