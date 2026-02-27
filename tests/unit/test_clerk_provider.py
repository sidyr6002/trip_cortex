from unittest.mock import MagicMock, patch

import jwt
import pytest

from core.auth.clerk_provider import ClerkAuthProvider
from core.auth.interface import AuthUser
from core.errors import AuthenticationError


@pytest.fixture
def mock_clerk_user():
    user = MagicMock()
    user.id = "user_123"
    user.first_name = "Jane"
    user.last_name = "Doe"
    user.username = "janedoe"
    user.email_addresses = [MagicMock(email_address="jane@example.com")]
    user.public_metadata = {"roles": ["employee"], "department": "engineering"}
    return user


@pytest.mark.asyncio
async def test_verify_token_valid(mock_clerk_user):
    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.return_value = mock_clerk_user
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        token = jwt.encode({"sub": "user_123"}, "secret", algorithm="HS256")

        result = await provider.verify_token(token)

        assert isinstance(result, AuthUser)
        assert result.user_id == "user_123"
        assert result.employee_id == "user_123"
        assert result.email == "jane@example.com"
        assert result.name == "Jane Doe"
        assert result.roles == ["employee"]


@pytest.mark.asyncio
async def test_verify_token_invalid():
    with patch("core.auth.clerk_provider.Clerk"):
        provider = ClerkAuthProvider(secret_key="sk_test_mock")

        with pytest.raises(AuthenticationError, match="Token verification failed"):
            await provider.verify_token("invalid_token")


@pytest.mark.asyncio
async def test_get_user_success(mock_clerk_user):
    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.return_value = mock_clerk_user
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        result = await provider.get_user("user_123")

        assert result.user_id == "user_123"
        assert result.email == "jane@example.com"
        assert result.name == "Jane Doe"
        assert result.roles == ["employee"]
        assert result.metadata["department"] == "engineering"


@pytest.mark.asyncio
async def test_get_user_no_email(mock_clerk_user):
    mock_clerk_user.email_addresses = []

    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.return_value = mock_clerk_user
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        result = await provider.get_user("user_123")

        assert result.email == ""


@pytest.mark.asyncio
async def test_get_user_no_name(mock_clerk_user):
    mock_clerk_user.first_name = None
    mock_clerk_user.last_name = None

    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.return_value = mock_clerk_user
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        result = await provider.get_user("user_123")

        assert result.name == "janedoe"


@pytest.mark.asyncio
async def test_get_user_default_roles(mock_clerk_user):
    mock_clerk_user.public_metadata = {}

    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.return_value = mock_clerk_user
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        result = await provider.get_user("user_123")

        assert result.roles == ["employee"]


@pytest.mark.asyncio
async def test_get_user_api_error():
    with patch("core.auth.clerk_provider.Clerk") as mock_clerk_class:
        mock_client = MagicMock()
        mock_client.users.get.side_effect = Exception("API error")
        mock_clerk_class.return_value = mock_client

        provider = ClerkAuthProvider(secret_key="sk_test_mock")

        with pytest.raises(AuthenticationError, match="Failed to fetch user"):
            await provider.get_user("user_123")


@pytest.mark.asyncio
async def test_decode_claims_valid():
    with patch("core.auth.clerk_provider.Clerk"):
        provider = ClerkAuthProvider(secret_key="sk_test_mock")
        token = jwt.encode({"sub": "user_123", "exp": 9999999999}, "secret", algorithm="HS256")

        result = await provider.decode_claims(token)

        assert result["sub"] == "user_123"


@pytest.mark.asyncio
async def test_decode_claims_invalid():
    with patch("core.auth.clerk_provider.Clerk"):
        provider = ClerkAuthProvider(secret_key="sk_test_mock")

        with pytest.raises(AuthenticationError, match="Invalid token"):
            await provider.decode_claims("not_a_jwt")
