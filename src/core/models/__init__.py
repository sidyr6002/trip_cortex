"""
Pydantic models for Trip Cortex.
"""

from core.models.booking import (
    BookingConfirmation,
    BookingInput,
    BookingOutput,
    BookingParameters,
    BookingPlan,
    PassengerInfo,
    PolicyConstraints,
    PolicySource,
    ReasoningRequest,
    ReasoningResult,
    ThinkingEffort,
)
from core.models.circuit_breaker import CircuitBreakerState, CircuitState
from core.models.flight import FlightOption, FlightSearchInput, FlightSearchOutput, FlightSearchResult
from core.models.ingestion import (
    BdaEntity,
    BdaProjectResult,
    BdaStatusResult,
    EmbeddingMessage,
    EmbeddingResult,
    FailedEntity,
    IngestionCompleteResult,
    IngestionRequest,
    IngestionStartResult,
)
from core.models.retrieval import PolicyChunkResult

# Resolve forward references after all models are imported
BookingInput.model_rebuild()

__all__ = [
    "BookingConfirmation",
    "BookingInput",
    "BookingOutput",
    "BookingPlan",
    "BookingParameters",
    "PassengerInfo",
    "PolicyConstraints",
    "PolicySource",
    "PolicyChunkResult",
    "FlightOption",
    "FlightSearchResult",
    "FlightSearchInput",
    "FlightSearchOutput",
    "ReasoningRequest",
    "ReasoningResult",
    "ThinkingEffort",
    "BdaProjectResult",
    "IngestionRequest",
    "IngestionStartResult",
    "BdaStatusResult",
    "IngestionCompleteResult",
    "BdaEntity",
    "FailedEntity",
    "EmbeddingMessage",
    "EmbeddingResult",
    "CircuitState",
    "CircuitBreakerState",
]
