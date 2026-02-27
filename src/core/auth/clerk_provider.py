import jwt
from clerk_backend_api import Clerk, authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions

from core.errors import AuthenticationError

from .interface import AuthProvider, AuthUser


class _FakeRequest:
    """Adapts a raw Bearer token to the Requestish protocol expected by Clerk SDK."""

    def __init__(self, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}


class ClerkAuthProvider(AuthProvider):
    def __init__(self, secret_key: str):
        self._client = Clerk(bearer_auth=secret_key)
        self._secret_key = secret_key

    async def verify_token(self, token: str) -> AuthUser:
        try:
            request_state = authenticate_request(
                _FakeRequest(token),
                AuthenticateRequestOptions(secret_key=self._secret_key),
            )
            if not request_state.is_signed_in or request_state.payload is None:
                raise AuthenticationError(
                    f"Token verification failed: {request_state.message or 'unknown'}"
                )
            user_id = str(request_state.payload["sub"])
            return await self.get_user(user_id)
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {e}") from e

    async def get_user(self, user_id: str) -> AuthUser:
        try:
            user = self._client.users.get(user_id=user_id)
            metadata = dict(user.public_metadata) if user.public_metadata else {}
            roles = (
                metadata.get("roles", ["employee"])
                if isinstance(metadata.get("roles"), list)
                else ["employee"]
            )
            return AuthUser(
                user_id=user.id,
                email=user.email_addresses[0].email_address if user.email_addresses else "",
                name=f"{user.first_name or ''} {user.last_name or ''}".strip()
                or user.username
                or "",
                roles=roles,
                employee_id=user.id,
                metadata={k: str(v) for k, v in metadata.items()},
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to fetch user: {e}") from e

    async def decode_claims(self, token: str) -> dict[str, object]:
        """Decode JWT claims WITHOUT signature verification. For logging/routing only."""
        try:
            decoded: dict[str, object] = jwt.decode(
                token, options={"verify_signature": False}
            )
            return decoded
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e
