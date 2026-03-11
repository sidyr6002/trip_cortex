"""Lambda handler for completing ingestion."""

from typing import Any

from core.clients import get_bda_runtime_client
from core.config import get_config
from core.db.aurora import AuroraClient
from core.services.ingestion import IngestionService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Mark ingestion as complete."""
    config = get_config()
    policy_id = event["policy_id"]
    output_s3_uri = event["output_s3_uri"]

    aurora_client = AuroraClient(config)
    aurora_client.connect()
    try:
        service = IngestionService(get_bda_runtime_client(), aurora_client)
        result = service.complete_ingestion(policy_id, output_s3_uri)
        return result.model_dump()
    finally:
        aurora_client.disconnect()
