from abc import ABC, abstractmethod

from pydantic import BaseModel


class AuthUser(BaseModel):
    user_id: str
    email: str
    name: str
    roles: list[str]
    employee_id: str
    metadata: dict[str, str]


class AuthProvider(ABC):
    @abstractmethod
    async def verify_token(self, token: str) -> AuthUser: ...

    @abstractmethod
    async def get_user(self, user_id: str) -> AuthUser: ...

    @abstractmethod
    async def decode_claims(self, token: str) -> dict[str, object]: ...


def get_auth_provider() -> AuthProvider:
    from core.config import get_config

    config = get_config()
    clerk_secret = config.clerk_secret_key
    if not clerk_secret:
        raise ValueError("CLERK_SECRET_KEY not configured")

    from core.auth.clerk_provider import ClerkAuthProvider

    return ClerkAuthProvider(secret_key=clerk_secret)
