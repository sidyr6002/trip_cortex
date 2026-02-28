from os import environ

import boto3
from pydantic import BaseModel, ConfigDict

_cached_clerk_secret: str | None = None


def _resolve_clerk_secret() -> str:
    """Fetch Clerk secret from Secrets Manager at runtime, with caching."""
    global _cached_clerk_secret
    if _cached_clerk_secret is not None:
        return _cached_clerk_secret

    # Local dev: use env var directly
    direct = environ.get("CLERK_SECRET_KEY", "")
    if direct:
        _cached_clerk_secret = direct
        return direct

    # Deployed: fetch from Secrets Manager by ARN
    arn = environ.get("CLERK_SECRET_ARN", "")
    if not arn:
        return ""

    client = boto3.client("secretsmanager")
    _cached_clerk_secret = client.get_secret_value(SecretId=arn)["SecretString"]
    return _cached_clerk_secret


class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    aws_region: str
    aurora_host: str
    aurora_port: int
    aurora_database: str
    aurora_user: str
    aurora_password: str
    dynamodb_endpoint: str | None = None
    aurora_secret_arn: str | None = None
    bookings_table: str
    connections_table: str
    audit_log_table: str
    nova_lite_model_id: str
    nova_embeddings_model_id: str
    clerk_secret_key: str = ""
    environment: str
    websocket_endpoint: str = ""


_cached_config: Config | None = None


def _reset_config() -> None:
    """Reset cached config — for testing only."""
    global _cached_config, _cached_clerk_secret
    _cached_config = None
    _cached_clerk_secret = None


def get_config() -> Config:
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    _cached_config = Config(
        aws_region=environ.get("AWS_REGION", "us-east-1"),
        aurora_host=environ.get("AURORA_HOST", "localhost"),
        aurora_port=int(environ.get("AURORA_PORT", "5432")),
        aurora_database=environ.get("AURORA_DATABASE", "tripcortex"),
        aurora_user=environ.get("AURORA_USER", "tripcortex"),
        aurora_password=environ.get("AURORA_PASSWORD", "localdev"),
        dynamodb_endpoint=environ.get("DYNAMODB_ENDPOINT"),
        aurora_secret_arn=environ.get("AURORA_SECRET_ARN"),
        bookings_table=environ.get("BOOKINGS_TABLE", "Bookings"),
        connections_table=environ.get("CONNECTIONS_TABLE", "Connections"),
        audit_log_table=environ.get("AUDIT_LOG_TABLE", "AuditLog"),
        nova_lite_model_id=environ.get("NOVA_LITE_MODEL_ID", "us.amazon.nova-2-lite-v1:0"),
        nova_embeddings_model_id=environ.get("NOVA_EMBEDDINGS_MODEL_ID", "amazon.nova-2-multimodal-embeddings-v1:0"),
        clerk_secret_key=_resolve_clerk_secret(),
        environment=environ.get("ENVIRONMENT", "local"),
        websocket_endpoint=environ.get("WEBSOCKET_ENDPOINT", ""),
    )
    return _cached_config
