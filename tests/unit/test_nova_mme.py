"""Unit tests for invoke_nova_mme shared helper."""

import json
from unittest.mock import MagicMock, call

import pytest
from botocore.exceptions import ClientError

from core.errors import PolicyRetrievalError
from core.services.nova_mme import invoke_nova_mme


def _make_client(vector: list[float] | None = None, error_code: str | None = None, fail_twice: bool = False):
    """Build a mock bedrock-runtime client."""
    client = MagicMock()
    success_response = {
        "body": MagicMock(read=lambda: json.dumps({"embeddings": [{"embedding": vector or [0.1] * 1024}]}).encode())
    }
    error = ClientError({"Error": {"Code": error_code or "ThrottlingException", "Message": ""}}, "InvokeModel")

    if fail_twice:
        client.invoke_model.side_effect = [error, error]
    elif error_code and not fail_twice:
        client.invoke_model.side_effect = error
    else:
        client.invoke_model.return_value = success_response

    return client, success_response, error


def _make_retry_client(error_code: str, success_vector: list[float]):
    """Client that fails once with error_code then succeeds."""
    client = MagicMock()
    error = ClientError({"Error": {"Code": error_code, "Message": ""}}, "InvokeModel")
    success = {
        "body": MagicMock(read=lambda: json.dumps({"embeddings": [{"embedding": success_vector}]}).encode())
    }
    client.invoke_model.side_effect = [error, success]
    return client


def test_successful_embedding_returns_correct_vector():
    vector = [0.5] * 1024
    client, _, _ = _make_client(vector=vector)
    result = invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    assert result == vector
    assert len(result) == 1024


def test_throttling_retries_and_succeeds(monkeypatch):
    monkeypatch.setattr("core.services.nova_mme.time.sleep", MagicMock())
    vector = [0.2] * 1024
    client = _make_retry_client("ThrottlingException", vector)
    result = invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    assert result == vector
    assert client.invoke_model.call_count == 2


def test_service_unavailable_retries_and_succeeds(monkeypatch):
    monkeypatch.setattr("core.services.nova_mme.time.sleep", MagicMock())
    vector = [0.3] * 1024
    client = _make_retry_client("ServiceUnavailableException", vector)
    result = invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    assert result == vector
    assert client.invoke_model.call_count == 2


def test_non_retryable_error_raises_immediately():
    client, _, _ = _make_client(error_code="ValidationException")
    with pytest.raises(PolicyRetrievalError):
        invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    assert client.invoke_model.call_count == 1


def test_throttling_twice_raises_policy_retrieval_error(monkeypatch):
    monkeypatch.setattr("core.services.nova_mme.time.sleep", MagicMock())
    client, _, _ = _make_client(error_code="ThrottlingException", fail_twice=True)
    with pytest.raises(PolicyRetrievalError):
        invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    assert client.invoke_model.call_count == 2


def test_purpose_passed_correctly_in_request_body():
    vector = [0.1] * 1024
    client, _, _ = _make_client(vector=vector)
    invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    call_kwargs = client.invoke_model.call_args
    body = json.loads(call_kwargs.kwargs["body"])
    assert body["singleEmbeddingParams"]["embeddingPurpose"] == "GENERIC_RETRIEVAL"
    assert body["singleEmbeddingParams"]["embeddingDimension"] == 1024


def test_retry_sleeps_200ms(monkeypatch):
    mock_sleep = MagicMock()
    monkeypatch.setattr("core.services.nova_mme.time.sleep", mock_sleep)
    vector = [0.1] * 1024
    client = _make_retry_client("ThrottlingException", vector)
    invoke_nova_mme(client, "model-id", "fly to NYC", "GENERIC_RETRIEVAL")
    mock_sleep.assert_called_once_with(0.2)
