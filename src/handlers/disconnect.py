"""WebSocket $disconnect handler."""

import logging
from typing import Any

import boto3

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
        dynamo_client = boto3.client("dynamodb", endpoint_url=config.dynamodb_endpoint)
        delete_connection(connection_id, dynamo_client, config.connections_table)
        logger.info("Deleted connection %s", connection_id)
    except Exception:
        logger.exception("Failed to delete connection %s", connection_id)

    return {"statusCode": 200}
