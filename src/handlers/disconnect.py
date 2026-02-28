"""WebSocket $disconnect handler."""

import logging
from typing import Any

from core.clients import get_dynamo_client
from core.config import get_config
from core.services.connection import delete_connection

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: object) -> dict[str, int]:
    """Clean up connection on disconnect.

    Always returns 200 — API Gateway doesn't retry $disconnect
    and the connection is already closed.
    """
    connection_id = event["requestContext"]["connectionId"]

    try:
        config = get_config()
        delete_connection(connection_id, get_dynamo_client(), config.connections_table)
        logger.info("Deleted connection %s", connection_id)
    except Exception:
        logger.exception("Failed to delete connection %s", connection_id)

    return {"statusCode": 200}
