"""Unit tests for get_policy_retrieval_service() factory."""

import os
from unittest.mock import patch

from core.clients import get_policy_retrieval_service
from core.config import _reset_config
from core.services.policy_retrieval import PolicyRetrievalService


def setup_function():
    _reset_config()


def teardown_function():
    _reset_config()


def test_factory_returns_policy_retrieval_service():
    with patch("boto3.client"), patch.dict(os.environ, {}, clear=False):
        svc = get_policy_retrieval_service()
    assert isinstance(svc, PolicyRetrievalService)


def test_factory_wires_correct_model_id():
    model_id = "amazon.nova-2-multimodal-embeddings-v1:0"
    with patch("boto3.client"), patch.dict(os.environ, {"NOVA_EMBEDDINGS_MODEL_ID": model_id}):
        svc = get_policy_retrieval_service()
    assert svc._query_embedding_service.model_id == model_id


def test_factory_wires_config():
    with patch("boto3.client"), patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "0.70"}):
        svc = get_policy_retrieval_service()
    assert svc._config.similarity_threshold == 0.70
