from core.errors import (
    AuthenticationError,
    BookingError,
    ErrorCode,
    PolicyRetrievalError,
    ReasoningError,
    TripCortexError,
    USER_MESSAGES,
    ValidationError,
)


def test_all_error_codes_have_user_message():
    for code in ErrorCode:
        assert code in USER_MESSAGES


def test_user_message_lookup():
    err = TripCortexError("pgvector connection timeout", code=ErrorCode.RETRIEVAL_FAILED)
    assert err.user_message == "Unable to retrieve travel policies. Please try again."


def test_subclasses_inherit_user_message():
    assert AuthenticationError("bad token", code=ErrorCode.AUTH_FAILED).user_message == USER_MESSAGES[ErrorCode.AUTH_FAILED]
    assert PolicyRetrievalError("miss", code=ErrorCode.NO_POLICY_FOUND).user_message == USER_MESSAGES[ErrorCode.NO_POLICY_FOUND]
    assert ReasoningError("fail", code=ErrorCode.REASONING_FAILED).user_message == USER_MESSAGES[ErrorCode.REASONING_FAILED]
    assert BookingError("fail", code=ErrorCode.BOOKING_FAILED).user_message == USER_MESSAGES[ErrorCode.BOOKING_FAILED]
    assert ValidationError("bad", code=ErrorCode.VALIDATION_ERROR).user_message == USER_MESSAGES[ErrorCode.VALIDATION_ERROR]


def test_user_message_never_exposes_internal_message():
    internal = "SELECT * FROM policy_chunks WHERE id = 'secret'"
    err = TripCortexError(internal, code=ErrorCode.RETRIEVAL_FAILED)
    assert internal not in err.user_message
