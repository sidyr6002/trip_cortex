"""Authentication abstraction layer."""

from core.auth.interface import AuthProvider, AuthUser, get_auth_provider

__all__ = ["AuthProvider", "AuthUser", "get_auth_provider"]
