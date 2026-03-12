"""Unit tests for generate_embeddings handler."""

from unittest.mock import MagicMock, patch

import pytest

from core.errors import PolicyRetrievalError
from core.models.ingestion import EmbeddingResult


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


def test_handler_happy_path(mock_config, mock_aurora_client, mock_embedding_service):
    """Test handler with successful embedding generation."""
    with patch("handlers.generate_embeddings.get_config", return_value=mock_config), \
         patch("handlers.generate_embeddings.AuroraClient", return_value=mock_aurora_client), \
         patch("handlers.generate_embeddings.EmbeddingService", return_value=mock_embedding_service), \
         patch("handlers.generate_embeddings.get_bedrock_runtime_client"), \
         patch("handlers.generate_embeddings.get_s3_client"):

        from handlers.generate_embeddings import handler

        # Mock service result
        result = EmbeddingResult(
            policy_id="test-policy-id",
            chunks_created=5,
            chunks_failed=0,
            entity_types={"text": 3, "table": 2},
            failed_entities=[],
        )
        mock_embedding_service.generate_embeddings.return_value = result

        event = {
            "policy_id": "test-policy-id",
            "output_s3_uri": "s3://bucket/prefix/",
        }

        response = handler(event, None)

        assert response["policy_id"] == "test-policy-id"
        assert response["chunks_created"] == 5
        assert response["chunks_failed"] == 0
        assert response["entity_types"] == {"text": 3, "table": 2}
        assert response["failed_entities"] == []

        # Verify Aurora connect/disconnect
        mock_aurora_client.connect.assert_called_once()
        mock_aurora_client.disconnect.assert_called_once()


def test_handler_propagates_service_error(mock_config, mock_aurora_client, mock_embedding_service):
    """Test that service errors propagate."""
    with patch("handlers.generate_embeddings.get_config", return_value=mock_config), \
         patch("handlers.generate_embeddings.AuroraClient", return_value=mock_aurora_client), \
         patch("handlers.generate_embeddings.EmbeddingService", return_value=mock_embedding_service), \
         patch("handlers.generate_embeddings.get_bedrock_runtime_client"), \
         patch("handlers.generate_embeddings.get_s3_client"):

        from handlers.generate_embeddings import handler

        # Mock service to raise error
        mock_embedding_service.generate_embeddings.side_effect = PolicyRetrievalError(
            "Test error", code="RETRIEVAL_FAILED"
        )

        event = {
            "policy_id": "test-policy-id",
            "output_s3_uri": "s3://bucket/prefix/",
        }

        with pytest.raises(PolicyRetrievalError):
            handler(event, None)


def test_handler_aurora_disconnect_on_error(mock_config, mock_aurora_client, mock_embedding_service):
    """Test that Aurora disconnect is called even on error."""
    with patch("handlers.generate_embeddings.get_config", return_value=mock_config), \
         patch("handlers.generate_embeddings.AuroraClient", return_value=mock_aurora_client), \
         patch("handlers.generate_embeddings.EmbeddingService", return_value=mock_embedding_service), \
         patch("handlers.generate_embeddings.get_bedrock_runtime_client"), \
         patch("handlers.generate_embeddings.get_s3_client"):

        from handlers.generate_embeddings import handler

        # Mock service to raise error
        mock_embedding_service.generate_embeddings.side_effect = PolicyRetrievalError(
            "Test error", code="RETRIEVAL_FAILED"
        )

        event = {
            "policy_id": "test-policy-id",
            "output_s3_uri": "s3://bucket/prefix/",
        }

        try:
            handler(event, None)
        except PolicyRetrievalError:
            pass

        # Verify disconnect was called despite error
        mock_aurora_client.disconnect.assert_called_once()
