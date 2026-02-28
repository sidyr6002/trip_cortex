"""WebSocket heartbeat handler — prevents idle timeout."""

import logging
from typing import Any

import boto3

from core.config import get_config
from core.services.connection import cleanup_stale_connections

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Ping all active connections and clean up stale ones."""
    config = get_config()

    dynamo_client = boto3.client("dynamodb", endpoint_url=config.dynamodb_endpoint)
    apigw_client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=config.websocket_endpoint,
    )

    result = cleanup_stale_connections(dynamo_client, apigw_client, config.connections_table)

    logger.info(
        "Heartbeat complete: %d active, %d cleaned",
        result["active"],
        result["cleaned"],
    )

    return {
        "statusCode": 200,
        "body": f"Heartbeat: {result['active']} active, {result['cleaned']} cleaned",
    }
