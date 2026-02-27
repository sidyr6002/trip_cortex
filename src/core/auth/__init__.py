"""Authentication abstraction layer."""

from core.auth.clerk_provider import ClerkAuthProvider
from core.auth.interface import AuthProvider, AuthUser, get_auth_provider

__all__ = ["AuthProvider", "AuthUser", "ClerkAuthProvider", "get_auth_provider"]
