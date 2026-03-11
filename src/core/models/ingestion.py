"""Models for the ingestion pipeline."""

from typing import Literal

from pydantic import BaseModel


class BdaProjectResult(BaseModel):
    """Result of BDA project creation or retrieval."""

    project_arn: str
    project_name: str
    status: Literal["created", "existing"]
