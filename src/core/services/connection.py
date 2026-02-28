"""Connection management service for WebSocket connections."""

import json
import logging
from time import time
from typing import Any

logger = logging.getLogger(__name__)


def store_connection(connection_id: str, employee_id: str, dynamo_client: Any, connections_table: str) -> None:
    """Store WebSocket connection with 24-hour TTL."""
    ttl = int(time()) + 86400  # 24 hours from now
    dynamo_client.put_item(
        TableName=connections_table,
        Item={"connectionId": {"S": connection_id}, "employeeId": {"S": employee_id}, "ttl": {"N": str(ttl)}},
    )


def delete_connection(connection_id: str, dynamo_client: Any, connections_table: str) -> None:
    """Delete WebSocket connection from DynamoDB."""
    dynamo_client.delete_item(
        TableName=connections_table,
        Key={"connectionId": {"S": connection_id}},
    )


def cleanup_stale_connections(
    dynamo_client: Any,
    apigw_client: Any,
    connections_table: str,
) -> dict[str, int]:
    """Ping all connections and delete stale ones."""
    active_count = 0
    stale_count = 0
    last_key = None

    while True:
        scan_kwargs: dict[str, Any] = {"TableName": connections_table}
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key

        response = dynamo_client.scan(**scan_kwargs)

        for conn in response.get("Items", []):
            connection_id = conn["connectionId"]["S"]
            try:
                apigw_client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps({"type": "heartbeat", "timestamp": int(time())}).encode(),
                )
                active_count += 1
            except apigw_client.exceptions.GoneException:
                delete_connection(connection_id, dynamo_client, connections_table)
                stale_count += 1
                logger.info("Cleaned stale connection %s", connection_id)
            except Exception:
                logger.exception("Error pinging connection %s", connection_id)

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break

    return {"active": active_count, "cleaned": stale_count}
