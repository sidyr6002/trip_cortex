"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pydantic
import pytest

from core.config import _reset_config, get_config


@pytest.fixture(autouse=True)
def _clear_config_cache():
    _reset_config()
    yield
    _reset_config()


def test_get_config_with_dynamodb_endpoint():
    """Test that get_config reads DYNAMODB_ENDPOINT when set."""
    with patch.dict(os.environ, {"DYNAMODB_ENDPOINT": "http://localhost:8000"}):
        config = get_config()
        assert config.dynamodb_endpoint == "http://localhost:8000"


def test_get_config_without_dynamodb_endpoint():
    """Test that get_config returns None when DYNAMODB_ENDPOINT is not set."""
    with patch.dict(os.environ, {}, clear=True):
        config = get_config()
        assert config.dynamodb_endpoint is None


def test_get_config_defaults():
    """Test that get_config provides sensible defaults."""
    with patch.dict(os.environ, {}, clear=True):
        config = get_config()
        assert config.aws_region == "us-east-1"
        assert config.aurora_host == "localhost"
        assert config.aurora_port == 5432
        assert config.environment == "local"
        assert config.dynamodb_endpoint is None


def test_aurora_port_string_coercion():
    with patch.dict(os.environ, {"AURORA_PORT": "5433"}, clear=False):
        config = get_config()
        assert config.aurora_port == 5433
        assert isinstance(config.aurora_port, int)


def test_config_is_immutable():
    with patch.dict(os.environ, {}, clear=True):
        config = get_config()
        with pytest.raises(pydantic.ValidationError):
            config.aws_region = "eu-west-1"  # type: ignore[misc]


def test_retrieval_config_defaults():
    with patch.dict(os.environ, {}, clear=True):
        config = get_config()
        assert config.similarity_threshold == 0.65
        assert config.high_confidence_threshold == 0.75
        assert config.retrieval_top_k == 5


def test_retrieval_config_custom_env_vars():
    with patch.dict(os.environ, {
        "SIMILARITY_THRESHOLD": "0.70",
        "HIGH_CONFIDENCE_THRESHOLD": "0.85",
        "RETRIEVAL_TOP_K": "10",
    }):
        config = get_config()
        assert config.similarity_threshold == 0.70
        assert config.high_confidence_threshold == 0.85
        assert config.retrieval_top_k == 10


def test_retrieval_config_invalid_type_raises():
    with patch.dict(os.environ, {"SIMILARITY_THRESHOLD": "not-a-float"}):
        with pytest.raises((ValueError, pydantic.ValidationError)):
            get_config()
