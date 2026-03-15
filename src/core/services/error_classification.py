"""Classify Nova Act exceptions into deterministic recovery strategies."""

from enum import Enum

import structlog

log = structlog.get_logger()


class RecoveryStrategy(str, Enum):
    REORIENT = "REORIENT"
    RETRY_WITH_WAIT = "RETRY_WITH_WAIT"
    DEEP_LINK_FALLBACK = "DEEP_LINK_FALLBACK"
    ABORT = "ABORT"


class ClassifiedError:
    __slots__ = ("error_type", "strategy", "wait_seconds", "warning")

    def __init__(self, error_type: str, strategy: RecoveryStrategy, wait_seconds: float, warning: str) -> None:
        self.error_type = error_type
        self.strategy = strategy
        self.wait_seconds = wait_seconds
        self.warning = warning


def classify_nova_act_error(exc: Exception, attempt: int, max_retries: int = 2) -> ClassifiedError:
    """Map a Nova Act exception to a recovery strategy.

    Import Nova Act types locally so unit tests run without nova-act installed.
    """
    from nova_act import (
        ActExceededMaxStepsError,
        ActGuardrailsError,
        ActRateLimitExceededError,
        ActStateGuardrailError,
        ActTimeoutError,
    )

    error_type = type(exc).__name__
    exhausted = attempt >= max_retries
    wait_seconds = 5.0 * (2.0 ** attempt)  # 5s, 10s, 20s …

    if isinstance(exc, (ActGuardrailsError, ActStateGuardrailError)):
        strategy, wait_seconds, warning = RecoveryStrategy.ABORT, 0.0, "GUARDRAIL_VIOLATION"
    elif isinstance(exc, ActExceededMaxStepsError):
        strategy = RecoveryStrategy.DEEP_LINK_FALLBACK if exhausted else RecoveryStrategy.REORIENT
        warning = "ACT_EXCEEDED_MAX_STEPS"
    elif isinstance(exc, (ActTimeoutError, ActRateLimitExceededError)):
        strategy = RecoveryStrategy.DEEP_LINK_FALLBACK if exhausted else RecoveryStrategy.RETRY_WITH_WAIT
        warning = "ACT_TIMEOUT" if isinstance(exc, ActTimeoutError) else "ACT_RATE_LIMITED"
    else:
        strategy, wait_seconds, warning = RecoveryStrategy.DEEP_LINK_FALLBACK, 0.0, "ACT_UNEXPECTED_ERROR"

    log.info(
        "nova_act_error_classified",
        error_type=error_type,
        attempt=attempt,
        strategy=strategy,
        wait_seconds=wait_seconds,
    )
    return ClassifiedError(error_type=error_type, strategy=strategy, wait_seconds=wait_seconds, warning=warning)
