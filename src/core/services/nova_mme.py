"""Shared Nova Multimodal Embeddings helper with single-retry for transient errors."""

import json
import time
from typing import Any

import structlog
from botocore.exceptions import ClientError

from core.errors import ErrorCode, PolicyRetrievalError

logger = structlog.get_logger()

_RETRYABLE_ERRORS = {"ThrottlingException", "ServiceUnavailableException"}


def invoke_nova_mme(
    client: Any,
    model_id: str,
    text: str,
    purpose: str,
    dimension: int = 1024,
) -> list[float]:
    """
    Invoke Nova Multimodal Embeddings for text input.

    Retries once on transient errors (429 ThrottlingException, 5xx ServiceUnavailableException).
    Raises PolicyRetrievalError on non-retryable errors or second failure.

    Args:
        client: boto3 bedrock-runtime client
        model_id: Nova MME model ID
        text: Input text to embed
        purpose: Embedding purpose — "GENERIC_INDEX" (ingestion) or "GENERIC_RETRIEVAL" (query)
        dimension: Embedding dimension (default 1024 per ADR-003)

    Returns:
        list[float] of length `dimension`
    """
    request_body = json.dumps(
        {
            "taskType": "SINGLE_EMBEDDING",
            "singleEmbeddingParams": {
                "embeddingPurpose": purpose,
                "embeddingDimension": dimension,
                "text": {"truncationMode": "END", "value": text},
            },
        }
    )

    for attempt in range(2):
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=request_body,
                accept="application/json",
                contentType="application/json",
            )
            return list(json.loads(response["body"].read())["embeddings"][0]["embedding"])
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if attempt == 0 and error_code in _RETRYABLE_ERRORS:
                logger.warning("nova_mme_retry", error_code=error_code, purpose=purpose, dimension=dimension)
                time.sleep(0.2)
                continue
            logger.error("nova_mme_failed", error_code=error_code, purpose=purpose, attempt=attempt)
            raise PolicyRetrievalError(
                f"Nova MME embedding failed: {error_code}",
                code=ErrorCode.RETRIEVAL_FAILED,
            ) from e
    raise PolicyRetrievalError("Nova MME embedding failed after retries", code=ErrorCode.RETRIEVAL_FAILED)
