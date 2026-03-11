"""Lambda handler for checking BDA job status."""

from typing import Any

from core.clients import get_bda_runtime_client
from core.config import get_config
from core.db.aurora import AuroraClient
from core.services.ingestion import IngestionService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Check BDA ingestion job status."""
    config = get_config()
    invocation_arn = event["invocation_arn"]

    aurora_client = AuroraClient(config)
    aurora_client.connect()
    try:
        service = IngestionService(get_bda_runtime_client(), aurora_client)
        result = service.check_bda_status(invocation_arn)
        return result.model_dump()
    finally:
        aurora_client.disconnect()
