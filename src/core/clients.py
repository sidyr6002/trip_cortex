"""Lazy-initialized boto3 clients — reused across warm Lambda invocations."""

from functools import lru_cache
from typing import Any

import boto3

from core.config import get_config


@lru_cache(maxsize=1)
def get_dynamo_client() -> Any:
    config = get_config()
    return boto3.client("dynamodb", endpoint_url=config.dynamodb_endpoint)


@lru_cache(maxsize=1)
def get_apigw_client() -> Any:
    config = get_config()
    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=config.websocket_endpoint,
    )
