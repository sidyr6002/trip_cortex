"""Lambda handler for failing ingestion."""

import logging
from typing import Any

from core.clients import get_bda_runtime_client
from core.config import get_config
from core.db.aurora import AuroraClient
from core.services.ingestion import IngestionService

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Mark ingestion as failed."""
    config = get_config()
    policy_id = event["policy_id"]
    error_message = event.get("error_message", "Unknown error")

    aurora_client = AuroraClient(config)
    aurora_client.connect()
    try:
        service = IngestionService(get_bda_runtime_client(), aurora_client)
        result = service.fail_ingestion(policy_id, error_message)
        return result.model_dump()
    except Exception as e:
        # Log but don't re-raise — avoid masking original BDA error
        logger.error(f"Failed to mark ingestion as failed: {str(e)}")
        return {"policy_id": policy_id, "status": "failed", "error": str(e)}
    finally:
        aurora_client.disconnect()
