"""WebSocket heartbeat handler — prevents idle timeout."""

import logging
from typing import Any

from core.clients import get_apigw_client, get_dynamo_client
from core.config import get_config
from core.services.connection import cleanup_stale_connections

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Ping all active connections and clean up stale ones."""
    config = get_config()

    result = cleanup_stale_connections(get_dynamo_client(), get_apigw_client(), config.connections_table)

    logger.info(
        "Heartbeat complete: %d active, %d cleaned",
        result["active"],
        result["cleaned"],
    )

    return {
        "statusCode": 200,
        "body": f"Heartbeat: {result['active']} active, {result['cleaned']} cleaned",
    }
