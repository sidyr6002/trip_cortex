"""Lambda handler for generating embeddings from BDA output."""

from typing import Any

from core.clients import get_bedrock_runtime_client, get_s3_client
from core.config import get_config
from core.db.aurora import AuroraClient
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
        result = service.generate_embeddings(event["policy_id"], event["output_s3_uri"])
        return result.model_dump()
    finally:
        aurora_client.disconnect()
