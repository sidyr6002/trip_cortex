"""Pydantic models for policy retrieval results."""

from pydantic import BaseModel


class PolicyChunkResult(BaseModel):
    id: str
    content_text: str | None
    section_title: str | None
    source_page: int | None
    content_type: str
    bda_entity_subtype: str | None
    similarity: float
