"""Lambda handler for generating embeddings from BDA output."""

import json
from typing import Any

from core.clients import get_bedrock_runtime_client, get_s3_client
from core.config import get_config
from core.db.aurora import AuroraClient
from core.models.ingestion import EmbeddingMessage
from core.services.embedding import EmbeddingService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Generate embeddings from BDA output and store in pgvector."""
    config = get_config()
    aurora_client = AuroraClient(config)

    try:
        aurora_client.connect()
        service = EmbeddingService(
            get_bedrock_runtime_client(),
            get_s3_client(),
            aurora_client,
            config.nova_embeddings_model_id,
        )

        if "Records" in event:
            msg = EmbeddingMessage.model_validate(json.loads(event["Records"][0]["body"]))
        else:
            msg = EmbeddingMessage.model_validate(event)

        result = service.generate_embeddings(msg.policy_id, msg.output_s3_uri)
        return result.model_dump()
    finally:
        aurora_client.disconnect()
