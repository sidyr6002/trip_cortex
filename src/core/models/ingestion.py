"""Models for the ingestion pipeline."""

from typing import Literal

from pydantic import BaseModel


class BdaProjectResult(BaseModel):
    """Result of BDA project creation or retrieval."""

    project_arn: str
    project_name: str
    status: Literal["created", "existing"]


class IngestionRequest(BaseModel):
    """Request to start ingestion of a policy document."""

    s3_uri: str
    file_name: str
    uploaded_by: str | None = None


class IngestionStartResult(BaseModel):
    """Result of starting BDA ingestion."""

    policy_id: str
    invocation_arn: str
    output_s3_uri: str


class BdaStatusResult(BaseModel):
    """Result of checking BDA job status."""

    invocation_arn: str
    status: Literal["IN_PROGRESS", "SUCCESS", "FAILED"]
    output_s3_uri: str | None = None
    error_message: str | None = None


class IngestionCompleteResult(BaseModel):
    """Result of completing or failing ingestion."""

    policy_id: str
    status: Literal["ready", "failed"]
    total_pages: int | None = None
    bda_output_s3_uri: str | None = None


class BdaEntity(BaseModel):
    """Parsed BDA document entity (TEXT, TABLE, or FIGURE)."""

    entity_type: Literal["TEXT", "TABLE", "FIGURE"]
    sub_type: str | None = None
    content_text: str | None = None
    markdown: str | None = None
    crop_image_s3_uri: str | None = None
    page_index: int | None = None
    section_title: str | None = None
    reading_order: int | None = None
    entity_id: str
    bounding_box: dict[str, object] | None = None


class FailedEntity(BaseModel):
    """Tracking for per-entity embedding failure."""

    entity_id: str
    entity_type: str
    error: str


class EmbeddingResult(BaseModel):
    """Result of embedding generation for a policy."""

    policy_id: str
    chunks_created: int
    chunks_failed: int
    entity_types: dict[str, int]  # e.g. {"text": 5, "table": 2, "figure": 1}
    failed_entities: list[FailedEntity]
