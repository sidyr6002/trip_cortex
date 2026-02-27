"""WebSocket $connect handler."""

from typing import Any

import boto3

from core.config import get_config
from core.services.connection import store_connection


def handler(event: dict[str, Any], context: object) -> dict[str, int]:
    connection_id = event["requestContext"]["connectionId"]
    employee_id = event["requestContext"]["authorizer"]["employeeId"]

    config = get_config()
    dynamo_client = boto3.client("dynamodb", endpoint_url=config.dynamodb_endpoint)

    store_connection(connection_id, employee_id, dynamo_client, config.connections_table)

    return {"statusCode": 200}

