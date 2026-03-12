"""Unit tests for get_query_embedding_service factory."""

import json
from unittest.mock import MagicMock, patch

from core.clients import get_query_embedding_service
from core.services.query_embedding import QueryEmbeddingService

_VECTOR = [0.2] * 1024
_MODEL_ID = "amazon.nova-2-multimodal-embeddings-v1:0"


def _mock_bedrock_response():
    return {
        "body": MagicMock(read=lambda: json.dumps({"embeddings": [{"embedding": _VECTOR}]}).encode())
    }


def test_factory_returns_query_embedding_service():
    with patch("core.clients.get_bedrock_runtime_client") as mock_client_fn, \
         patch("core.clients.get_config") as mock_config_fn:
        mock_config_fn.return_value = MagicMock(nova_embeddings_model_id=_MODEL_ID)
        mock_client_fn.return_value = MagicMock()
        svc = get_query_embedding_service()
    assert isinstance(svc, QueryEmbeddingService)


def test_factory_passes_model_id_from_config():
    with patch("core.clients.get_bedrock_runtime_client") as mock_client_fn, \
         patch("core.clients.get_config") as mock_config_fn:
        mock_config_fn.return_value = MagicMock(nova_embeddings_model_id=_MODEL_ID)
        mock_client_fn.return_value = MagicMock()
        svc = get_query_embedding_service()
    assert svc.model_id == _MODEL_ID


def test_full_call_chain_returns_vector():
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = _mock_bedrock_response()

    with patch("core.clients.get_bedrock_runtime_client", return_value=mock_client), \
         patch("core.clients.get_config") as mock_config_fn:
        mock_config_fn.return_value = MagicMock(nova_embeddings_model_id=_MODEL_ID)
        svc = get_query_embedding_service()
        result = svc.embed_query("book a flight to Chicago")

    assert result == _VECTOR
    assert mock_client.invoke_model.call_args.kwargs["modelId"] == _MODEL_ID
