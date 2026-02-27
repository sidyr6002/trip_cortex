import pytest

from core.auth import AuthProvider, AuthUser, get_auth_provider

VALID_USER = dict(
    user_id="user_123",
    email="employee@example.com",
    name="Jane Doe",
    roles=["employee"],
    employee_id="EMP001",
    metadata={"department": "engineering"},
)


def test_auth_user_valid():
    user = AuthUser(**VALID_USER)
    assert user.model_dump()["user_id"] == "user_123"


def test_auth_user_missing_name():
    with pytest.raises(Exception):
        AuthUser(**{k: v for k, v in VALID_USER.items() if k != "name"})


def test_auth_user_missing_roles():
    with pytest.raises(Exception):
        AuthUser(**{k: v for k, v in VALID_USER.items() if k != "roles"})


def test_auth_provider_is_abstract():
    with pytest.raises(TypeError):
        AuthProvider()  # type: ignore[abstract]


def test_auth_provider_concrete_subclass():
    class MockProvider(AuthProvider):
        async def verify_token(self, token: str) -> AuthUser:
            return AuthUser(**VALID_USER)

        async def get_user(self, user_id: str) -> AuthUser:
            return AuthUser(**VALID_USER)

        async def decode_claims(self, token: str) -> dict:
            return {"sub": "user_123"}

    provider = MockProvider()
    assert isinstance(provider, AuthProvider)


def test_get_auth_provider_raises():
    with pytest.raises(NotImplementedError):
        get_auth_provider()
