"""Lambda handler for checking BDA job status."""

from typing import Any

from core.clients import get_bda_runtime_client
from core.services.ingestion import IngestionService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Check BDA ingestion job status."""
    invocation_arn = event["invocation_arn"]

    service = IngestionService(get_bda_runtime_client(), aurora_client=None)  # type: ignore[arg-type]
    result = service.check_bda_status(invocation_arn)
    return result.model_dump()
