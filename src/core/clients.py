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


@lru_cache(maxsize=1)
def get_bda_client() -> Any:
    config = get_config()
    return boto3.client("bedrock-data-automation", region_name=config.aws_region)


@lru_cache(maxsize=1)
def get_bda_runtime_client() -> Any:
    config = get_config()
    return boto3.client("bedrock-data-automation-runtime", region_name=config.aws_region)


@lru_cache(maxsize=1)
def get_sfn_client() -> Any:
    config = get_config()
    return boto3.client("stepfunctions", region_name=config.aws_region)


@lru_cache(maxsize=1)
def get_bedrock_runtime_client() -> Any:
    config = get_config()
    return boto3.client("bedrock-runtime", region_name=config.aws_region)


@lru_cache(maxsize=1)
def get_s3_client() -> Any:
    config = get_config()
    return boto3.client("s3", region_name=config.aws_region)


def get_query_embedding_service() -> "QueryEmbeddingService":  # type: ignore[name-defined]
    from core.services.query_embedding import QueryEmbeddingService
    config = get_config()
    return QueryEmbeddingService(get_bedrock_runtime_client(), config.nova_embeddings_model_id)
