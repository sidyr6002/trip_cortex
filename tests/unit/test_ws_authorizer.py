"""Unit tests for WebSocket Lambda authorizer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.auth.interface import AuthUser
from core.errors import AuthenticationError
from handlers.ws_authorizer import handler


@pytest.fixture
def authorizer_event():
    return {
        "type": "REQUEST",
        "methodArn": "arn:aws:execute-api:us-east-1:123456789:abc123/$connect",
        "queryStringParameters": {"token": "valid_jwt_token"},
    }


@pytest.fixture
def mock_auth_user():
    return AuthUser(
        user_id="user_123",
        employee_id="emp_123",
        email="test@example.com",
        name="Test User",
        roles=["employee"],
        metadata={},
    )


def test_authorizer_valid_token(authorizer_event, mock_auth_user):
    with patch("handlers.ws_authorizer.get_auth_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.verify_token = AsyncMock(return_value=mock_auth_user)
        mock_get_provider.return_value = mock_provider

        result = handler(authorizer_event, None)

        assert result["principalId"] == "emp_123"
        assert result["policyDocument"]["Statement"][0]["Effect"] == "Allow"
        assert result["context"]["employeeId"] == "emp_123"


def test_authorizer_invalid_token(authorizer_event):
    with patch("handlers.ws_authorizer.get_auth_provider") as mock_get_provider:
        mock_provider = MagicMock()
        mock_provider.verify_token = AsyncMock(side_effect=AuthenticationError("Invalid token"))
        mock_get_provider.return_value = mock_provider

        result = handler(authorizer_event, None)

        assert result["principalId"] == "unauthorized"
        assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
        assert "context" not in result


def test_authorizer_missing_token(authorizer_event):
    authorizer_event["queryStringParameters"] = {}

    result = handler(authorizer_event, None)

    assert result["principalId"] == "unauthorized"
    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"


def test_authorizer_no_query_params(authorizer_event):
    authorizer_event["queryStringParameters"] = None

    result = handler(authorizer_event, None)

    assert result["principalId"] == "unauthorized"
    assert result["policyDocument"]["Statement"][0]["Effect"] == "Deny"
