"""Pydantic models for policy retrieval results."""

from enum import Enum

from pydantic import BaseModel, Field


class PolicyChunkResult(BaseModel):
    id: str
    content_text: str | None
    section_title: str | None
    source_page: int | None
    content_type: str
    bda_entity_subtype: str | None
    similarity: float


class QueryEmbeddingRequest(BaseModel):
    query_text: str = Field(min_length=1, max_length=10_000)
    employee_id: str = Field(min_length=1)


class QueryEmbeddingResult(BaseModel):
    embedding: list[float]
    model_id: str
    dimension: int
    latency_ms: float


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    LOW = "low"
    NONE = "none"


class ConfidenceAssessment(BaseModel):
    level: ConfidenceLevel
    max_similarity: float
    action: str


class RetrievalResult(BaseModel):
    chunks: list[PolicyChunkResult]
    confidence: ConfidenceAssessment
    context_text: str
    total_chunks: int
    latency_ms: float


class EmbedAndRetrieveRequest(BaseModel):
    booking_id: str = Field(min_length=1)
    employee_id: str = Field(min_length=1)
    user_query: str = Field(min_length=1, max_length=10_000)


class EmbedAndRetrieveResponse(BaseModel):
    booking_id: str
    employee_id: str
    user_query: str
    context_text: str
    confidence: ConfidenceAssessment
    total_chunks: int
    retrieval_latency_ms: float
