"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from core.config import get_config


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
