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


USER_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.AUTH_FAILED: "Authentication failed. Please sign in again.",
    ErrorCode.INVALID_TOKEN: "Your session has expired. Please sign in again.",
    ErrorCode.NO_POLICY_FOUND: "No travel policy found for your request. Please contact the travel team.",
    ErrorCode.RETRIEVAL_FAILED: "Unable to retrieve travel policies. Please try again.",
    ErrorCode.LOW_CONFIDENCE: "Travel policy match is uncertain. Strictest defaults will be applied.",
    ErrorCode.REASONING_FAILED: "Unable to process your booking request. Please try again.",
    ErrorCode.INVALID_PLAN: "Unable to generate a valid booking plan. Please rephrase your request.",
    ErrorCode.SEARCH_FAILED: "Flight search encountered an error. Please try again.",
    ErrorCode.BOOKING_FAILED: "Booking could not be completed. Please try again or contact the travel team.",
    ErrorCode.PORTAL_UNAVAILABLE: "The travel portal is temporarily unavailable. Please try again later.",
    ErrorCode.VALIDATION_ERROR: "Your request contains invalid information. Please check and try again.",
    ErrorCode.INVALID_REQUEST: "Invalid request format. Please try again.",
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred. Please try again.",
    ErrorCode.TIMEOUT: "The request timed out. Please try again.",
}


class TripCortexError(Exception):
    """Base exception for all Trip Cortex errors."""

    def __init__(self, message: str, code: ErrorCode = ErrorCode.INTERNAL_ERROR):
        self.message = message
        self.code = code
        super().__init__(message)

    @property
    def user_message(self) -> str:
        return USER_MESSAGES.get(self.code, USER_MESSAGES[ErrorCode.INTERNAL_ERROR])


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
