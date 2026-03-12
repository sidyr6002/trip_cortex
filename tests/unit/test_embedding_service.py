"""Unit tests for EmbeddingService."""

import json
from unittest.mock import MagicMock, call

import pytest

from core.services.embedding import EmbeddingService


@pytest.fixture
def mock_bedrock_client():
    return MagicMock()


@pytest.fixture
def mock_s3_client():
    return MagicMock()


@pytest.fixture
def mock_aurora_client():
    client = MagicMock()
    client.insert_chunks.return_value = 0
    return client


@pytest.fixture
def embedding_service(mock_bedrock_client, mock_s3_client, mock_aurora_client):
    return EmbeddingService(
        mock_bedrock_client,
        mock_s3_client,
        mock_aurora_client,
        "amazon.nova-2-multimodal-embeddings-v1:0",
    )


def _mock_s3(mock_s3_client, elements):
    mock_s3_client.list_objects_v2.return_value = {
        "Contents": [{"Key": "prefix/0/invocation-id/result.json"}]
    }
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps({"elements": elements}).encode())
    }


def _mock_bedrock(mock_bedrock_client):
    mock_bedrock_client.invoke_model.return_value = {
        "body": MagicMock(read=lambda: json.dumps({"embeddings": [{"embedding": [0.1] * 1024}]}).encode())
    }


def test_generate_embeddings_text_entities(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test embedding generation for TEXT entities."""
    _mock_s3(mock_s3_client, [
        {
            "id": "entity-1",
            "type": "TEXT",
            "representation": {"text": "Sample text", "markdown": "# Sample text"},
            "reading_order": 1,
            "locations": [{"page_index": 0, "bounding_box": {"x": 0, "y": 0}}],
        }
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 1

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.policy_id == "test-policy-id"
    assert result.chunks_created == 1
    assert result.chunks_failed == 0
    assert result.entity_types == {"text": 1}
    assert len(result.failed_entities) == 0

    request_body = json.loads(mock_bedrock_client.invoke_model.call_args.kwargs["body"])
    assert request_body["singleEmbeddingParams"]["embeddingDimension"] == 1024
    assert request_body["singleEmbeddingParams"]["embeddingPurpose"] == "GENERIC_INDEX"


def test_generate_embeddings_table_entities(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test embedding generation for TABLE entities."""
    _mock_s3(mock_s3_client, [
        {
            "id": "entity-1",
            "type": "TABLE",
            "representation": {"markdown": "| Col1 | Col2 |\n|------|------|", "text": "Table text"},
            "reading_order": 1,
            "locations": [{"page_index": 0}],
        }
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 1

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.chunks_created == 1
    assert result.entity_types == {"table": 1}


def test_generate_embeddings_figure_entities(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test embedding generation for FIGURE entities with image."""
    _mock_s3(mock_s3_client, [
        {
            "id": "entity-1",
            "type": "FIGURE",
            "crop_images": ["s3://bucket/figure-1.png"],
            "summary": "Figure summary",
            "reading_order": 1,
            "locations": [{"page_index": 0}],
        }
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 1

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.chunks_created == 1
    assert result.entity_types == {"figure": 1}

    request_body = json.loads(mock_bedrock_client.invoke_model.call_args.kwargs["body"])
    assert request_body["singleEmbeddingParams"]["image"]["detailLevel"] == "DOCUMENT_IMAGE"
    assert request_body["singleEmbeddingParams"]["image"]["source"]["s3Location"]["uri"] == "s3://bucket/figure-1.png"


def test_generate_embeddings_mixed_entities(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test embedding generation with mixed entity types."""
    _mock_s3(mock_s3_client, [
        {"id": "text-1", "type": "TEXT", "representation": {"text": "Text", "markdown": "# Text"}, "reading_order": 1, "locations": [{"page_index": 0}]},
        {"id": "table-1", "type": "TABLE", "representation": {"markdown": "| A | B |", "text": "Table"}, "reading_order": 2, "locations": [{"page_index": 0}]},
        {"id": "figure-1", "type": "FIGURE", "crop_images": ["s3://bucket/fig.png"], "summary": "Fig", "reading_order": 3, "locations": [{"page_index": 0}]},
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 3

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.chunks_created == 3
    assert result.entity_types == {"text": 1, "table": 1, "figure": 1}


def test_embed_text_request_body(embedding_service, mock_bedrock_client):
    """Verify exact Nova MME text request body."""
    _mock_bedrock(mock_bedrock_client)
    embedding_service._embed_text("Test text")

    request_body = json.loads(mock_bedrock_client.invoke_model.call_args.kwargs["body"])
    assert request_body["taskType"] == "SINGLE_EMBEDDING"
    assert request_body["singleEmbeddingParams"]["embeddingDimension"] == 1024
    assert request_body["singleEmbeddingParams"]["embeddingPurpose"] == "GENERIC_INDEX"
    assert request_body["singleEmbeddingParams"]["text"]["truncationMode"] == "END"
    assert request_body["singleEmbeddingParams"]["text"]["value"] == "Test text"


def test_embed_image_request_body(embedding_service, mock_bedrock_client):
    """Verify exact Nova MME image request body."""
    _mock_bedrock(mock_bedrock_client)
    embedding_service._embed_image("s3://bucket/image.png")

    request_body = json.loads(mock_bedrock_client.invoke_model.call_args.kwargs["body"])
    assert request_body["singleEmbeddingParams"]["embeddingDimension"] == 1024
    assert request_body["singleEmbeddingParams"]["embeddingPurpose"] == "GENERIC_INDEX"
    assert request_body["singleEmbeddingParams"]["image"]["detailLevel"] == "DOCUMENT_IMAGE"
    assert request_body["singleEmbeddingParams"]["image"]["format"] == "png"
    assert request_body["singleEmbeddingParams"]["image"]["source"]["s3Location"]["uri"] == "s3://bucket/image.png"


def test_skips_empty_entities(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test that entities with no content are skipped and tracked."""
    _mock_s3(mock_s3_client, [
        {"id": "empty-1", "type": "TEXT", "representation": {"text": None, "markdown": None}, "reading_order": 1, "locations": [{"page_index": 0}]}
    ])

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.chunks_created == 0
    assert result.chunks_failed == 1
    assert result.failed_entities[0].entity_id == "empty-1"


def test_partial_failure_tracking(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Test that one entity failure doesn't block others."""
    _mock_s3(mock_s3_client, [
        {"id": "good-1", "type": "TEXT", "representation": {"text": "Good text", "markdown": "# Good"}, "reading_order": 1, "locations": [{"page_index": 0}]},
        {"id": "bad-1", "type": "FIGURE", "crop_images": [], "summary": None, "reading_order": 2, "locations": [{"page_index": 0}]},
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 1

    result = embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    assert result.chunks_created == 1
    assert result.chunks_failed == 1
    assert result.failed_entities[0].entity_id == "bad-1"


def test_policy_status_updated_to_embedded(embedding_service, mock_bedrock_client, mock_s3_client, mock_aurora_client):
    """Verify aurora_client.update_policy_status is called with 'embedded'."""
    _mock_s3(mock_s3_client, [
        {"id": "entity-1", "type": "TEXT", "representation": {"text": "Text", "markdown": "# Text"}, "reading_order": 1, "locations": [{"page_index": 0}]}
    ])
    _mock_bedrock(mock_bedrock_client)
    mock_aurora_client.insert_chunks.return_value = 1

    embedding_service.generate_embeddings("test-policy-id", "s3://bucket/prefix/")

    mock_aurora_client.update_policy_status.assert_called_once_with("test-policy-id", "embedded", 1)
