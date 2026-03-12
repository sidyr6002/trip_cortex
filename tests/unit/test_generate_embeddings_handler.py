"""Unit tests for generate_embeddings handler."""

import json
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from core.errors import PolicyRetrievalError
from core.models.ingestion import EmbeddingResult

POLICY_ID = "test-policy-id"
OUTPUT_URI = "s3://bucket/bda-output/test-policy-id/"

DIRECT_EVENT = {"policy_id": POLICY_ID, "output_s3_uri": OUTPUT_URI}

SQS_EVENT = {
    "Records": [{"body": json.dumps({"policy_id": POLICY_ID, "output_s3_uri": OUTPUT_URI})}]
}

EMBEDDING_RESULT = EmbeddingResult(
    policy_id=POLICY_ID,
    chunks_created=5,
    chunks_failed=0,
    entity_types={"text": 3, "table": 2},
    failed_entities=[],
)


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.nova_embeddings_model_id = "amazon.nova-2-multimodal-embeddings-v1:0"
    return config


@pytest.fixture
def mock_aurora_client():
    client = MagicMock()
    return client


@pytest.fixture
def mock_embedding_service():
    return MagicMock()


def _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
    stack = ExitStack()
    stack.enter_context(patch("handlers.generate_embeddings.get_config", return_value=mock_config))
    stack.enter_context(patch("handlers.generate_embeddings.AuroraClient", return_value=mock_aurora_client))
    stack.enter_context(patch("handlers.generate_embeddings.EmbeddingService", return_value=mock_embedding_service))
    stack.enter_context(patch("handlers.generate_embeddings.get_bedrock_runtime_client"))
    stack.enter_context(patch("handlers.generate_embeddings.get_s3_client"))
    return stack


def test_handler_happy_path(mock_config, mock_aurora_client, mock_embedding_service):
    """Test handler with successful embedding generation (direct invocation)."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        mock_embedding_service.generate_embeddings.return_value = EMBEDDING_RESULT
        response = handler(DIRECT_EVENT, None)

        assert response["policy_id"] == POLICY_ID
        assert response["chunks_created"] == 5
        assert response["chunks_failed"] == 0
        assert response["entity_types"] == {"text": 3, "table": 2}
        assert response["failed_entities"] == []
        mock_aurora_client.connect.assert_called_once()
        mock_aurora_client.disconnect.assert_called_once()


def test_handler_sqs_event_happy_path(mock_config, mock_aurora_client, mock_embedding_service):
    """Test handler parses SQS event and calls service with correct args."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        mock_embedding_service.generate_embeddings.return_value = EMBEDDING_RESULT
        response = handler(SQS_EVENT, None)

        mock_embedding_service.generate_embeddings.assert_called_once_with(POLICY_ID, OUTPUT_URI)
        assert response["policy_id"] == POLICY_ID


def test_handler_sqs_event_invalid_body(mock_config, mock_aurora_client, mock_embedding_service):
    """Test that malformed SQS message body raises ValidationError."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        bad_event = {"Records": [{"body": json.dumps({"wrong_field": "value"})}]}
        with pytest.raises(ValidationError):
            handler(bad_event, None)


def test_handler_direct_invocation_still_works(mock_config, mock_aurora_client, mock_embedding_service):
    """Test backward compatibility: direct event format still works."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        mock_embedding_service.generate_embeddings.return_value = EMBEDDING_RESULT
        handler(DIRECT_EVENT, None)

        mock_embedding_service.generate_embeddings.assert_called_once_with(POLICY_ID, OUTPUT_URI)


def test_handler_propagates_service_error(mock_config, mock_aurora_client, mock_embedding_service):
    """Test that service errors propagate."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        mock_embedding_service.generate_embeddings.side_effect = PolicyRetrievalError(
            "Test error", code="RETRIEVAL_FAILED"
        )
        with pytest.raises(PolicyRetrievalError):
            handler(DIRECT_EVENT, None)


def test_handler_aurora_disconnect_on_error(mock_config, mock_aurora_client, mock_embedding_service):
    """Test that Aurora disconnect is called even on error."""
    with _patched_handler(mock_config, mock_aurora_client, mock_embedding_service):
        from handlers.generate_embeddings import handler

        mock_embedding_service.generate_embeddings.side_effect = PolicyRetrievalError(
            "Test error", code="RETRIEVAL_FAILED"
        )
        try:
            handler(DIRECT_EVENT, None)
        except PolicyRetrievalError:
            pass

        mock_aurora_client.disconnect.assert_called_once()

