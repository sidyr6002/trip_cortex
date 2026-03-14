"""Lazy-initialized boto3 clients — reused across warm Lambda invocations."""

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config as BotocoreConfig

from core.config import get_config

if TYPE_CHECKING:
    from core.services.policy_retrieval import PolicyRetrievalService
    from core.services.query_embedding import QueryEmbeddingService
    from core.services.reasoning import ReasoningService


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


@lru_cache(maxsize=1)
def get_acr_client() -> Any:
    config = get_config()
    return boto3.client(
        "bedrock-agentcore",
        region_name=config.aws_region,
        config=BotocoreConfig(read_timeout=580, connect_timeout=10),
    )


def get_query_embedding_service() -> "QueryEmbeddingService":
    from core.services.query_embedding import QueryEmbeddingService

    config = get_config()
    return QueryEmbeddingService(get_bedrock_runtime_client(), config.nova_embeddings_model_id)


def get_policy_retrieval_service() -> "PolicyRetrievalService":
    from core.db.aurora import AuroraClient
    from core.services.policy_retrieval import PolicyRetrievalService

    config = get_config()
    return PolicyRetrievalService(get_query_embedding_service(), AuroraClient(config), config)


def get_reasoning_service() -> "ReasoningService":
    from core.services.reasoning import ReasoningService

    config = get_config()
    return ReasoningService(get_bedrock_runtime_client(), config.nova_lite_model_id)
