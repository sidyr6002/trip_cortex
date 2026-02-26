"""
Authentication abstraction layer for Trip Cortex.

Provides a provider-agnostic interface for authentication that can be
implemented by different auth providers (Clerk, Cognito, etc.).

Usage:
    from core.auth import get_auth_provider, AuthUser
    
    provider = get_auth_provider()
    user = await provider.verify_token(jwt_token)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AuthUser:
    """Authenticated user information."""
    
    user_id: str
    email: str
    employee_id: str
    metadata: dict[str, str]


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    @abstractmethod
    async def verify_token(self, token: str) -> AuthUser:
        """
        Verify a JWT token and return user information.
        
        Args:
            token: JWT token from client
            
        Returns:
            AuthUser with verified user information
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> AuthUser:
        """
        Retrieve user information by user ID.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            AuthUser with user information
            
        Raises:
            AuthenticationError: If user not found
        """
        pass


def get_auth_provider() -> AuthProvider:
    """
    Factory function to get the configured auth provider.
    
    Returns:
        Configured AuthProvider instance (ClerkAuthProvider in production)
    """
    # TODO: Import and return ClerkAuthProvider once implemented
    raise NotImplementedError("Auth provider not yet implemented")
