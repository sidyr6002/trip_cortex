"""Query embedding service — converts user query text to a vector for similarity search."""

import time
from typing import Any

import structlog

from core.errors import ErrorCode, ValidationError
from core.services.nova_mme import invoke_nova_mme

logger = structlog.get_logger()

_MAX_TEXT_LENGTH = 10_000


class QueryEmbeddingService:
    """Generates Nova MME embeddings for user query text (GENERIC_RETRIEVAL purpose)."""

    def __init__(self, bedrock_runtime_client: Any, model_id: str) -> None:
        self.bedrock_runtime_client = bedrock_runtime_client
        self.model_id = model_id

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a user query string for pgvector similarity search.

        Args:
            text: Natural language query text (1–10,000 chars)

        Returns:
            1024-dimension embedding vector

        Raises:
            ValidationError: If text is empty or exceeds 10,000 characters
            PolicyRetrievalError: If Bedrock call fails after retry
        """
        if not text:
            raise ValidationError("Query text must not be empty", code=ErrorCode.VALIDATION_ERROR)
        if len(text) > _MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Query text exceeds maximum length of {_MAX_TEXT_LENGTH} characters",
                code=ErrorCode.VALIDATION_ERROR,
            )

        start = time.monotonic()
        vector = invoke_nova_mme(self.bedrock_runtime_client, self.model_id, text, purpose="GENERIC_RETRIEVAL")
        logger.info(
            "query_embedded",
            text_length=len(text),
            latency_ms=round((time.monotonic() - start) * 1000, 1),
        )
        return vector
