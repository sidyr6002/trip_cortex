from enum import Enum

from pydantic import BaseModel, ConfigDict


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerState(BaseModel):
    model_config = ConfigDict(frozen=True)

    circuit_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    recovery_timeout: int = 60
    ttl: int = 0
