"""WebSocket heartbeat handler — prevents idle timeout and cleans stale bookings."""

import logging
from typing import Any

from core.clients import get_apigw_client, get_dynamo_client, get_sfn_client
from core.config import get_config
from core.services.connection import cleanup_stale_connections
from core.services.stale_booking_cleanup import cleanup_stale_bookings

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Ping all active connections and clean up stale ones."""
    config = get_config()
    dynamo = get_dynamo_client()

    conn_result = cleanup_stale_connections(dynamo, get_apigw_client(), config.connections_table)
    booking_result = cleanup_stale_bookings(dynamo, get_sfn_client(), config.bookings_table)

    logger.info(
        "Heartbeat complete: %d active connections, %d cleaned, %d stale bookings resolved",
        conn_result["active"],
        conn_result["cleaned"],
        booking_result["resolved"],
    )

    return {
        "statusCode": 200,
        "body": (
            f"Heartbeat: {conn_result['active']} active, {conn_result['cleaned']} cleaned, "
            f"{booking_result['resolved']} stale bookings resolved"
        ),
    }
