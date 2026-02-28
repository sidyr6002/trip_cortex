"""WebSocket $connect handler."""

from typing import Any

from core.clients import get_dynamo_client
from core.config import get_config
from core.services.connection import store_connection


def handler(event: dict[str, Any], context: object) -> dict[str, int]:
    connection_id = event["requestContext"]["connectionId"]
    employee_id = event["requestContext"]["authorizer"]["employeeId"]

    config = get_config()
    store_connection(connection_id, employee_id, get_dynamo_client(), config.connections_table)

    return {"statusCode": 200}
