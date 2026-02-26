"""
Custom exceptions and error handling for Trip Cortex.

Defines application-specific exceptions with error codes for consistent
error handling across Lambda functions and client communication.

Usage:
    from core.errors import PolicyRetrievalError, ErrorCode
    
    raise PolicyRetrievalError("No policy chunks found", code=ErrorCode.NO_POLICY_FOUND)
"""

from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for client-facing error messages."""
    
    # Authentication errors
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # Policy retrieval errors
    NO_POLICY_FOUND = "NO_POLICY_FOUND"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    
    # Reasoning errors
    REASONING_FAILED = "REASONING_FAILED"
    INVALID_PLAN = "INVALID_PLAN"
    
    # Booking errors
    SEARCH_FAILED = "SEARCH_FAILED"
    BOOKING_FAILED = "BOOKING_FAILED"
    PORTAL_UNAVAILABLE = "PORTAL_UNAVAILABLE"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT = "TIMEOUT"


class TripCortexError(Exception):
    """Base exception for all Trip Cortex errors."""
    
    def __init__(self, message: str, code: ErrorCode = ErrorCode.INTERNAL_ERROR):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthenticationError(TripCortexError):
    """Authentication or authorization failed."""
    pass


class PolicyRetrievalError(TripCortexError):
    """Policy retrieval or embedding generation failed."""
    pass


class ReasoningError(TripCortexError):
    """Reasoning or plan generation failed."""
    pass


class BookingError(TripCortexError):
    """Flight search or booking operation failed."""
    pass


class ValidationError(TripCortexError):
    """Input validation or schema validation failed."""
    pass
