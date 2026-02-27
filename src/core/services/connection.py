"""Connection management service for WebSocket connections."""

from time import time
from typing import Any


def store_connection(connection_id: str, employee_id: str, dynamo_client: Any, connections_table: str) -> None:
    """Store WebSocket connection with 24-hour TTL."""
    ttl = int(time()) + 86400  # 24 hours from now
    dynamo_client.put_item(
        TableName=connections_table,
        Item={"connectionId": {"S": connection_id}, "employeeId": {"S": employee_id}, "ttl": {"N": str(ttl)}},
    )
