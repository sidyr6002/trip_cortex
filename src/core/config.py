"""
Configuration management for Trip Cortex.

Loads environment variables and provides typed configuration objects
for use across all Lambda functions and services.

Usage:
    from core.config import get_config
    
    config = get_config()
    bedrock_client = boto3.client('bedrock-runtime', region_name=config.aws_region)
"""

from dataclasses import dataclass
from os import environ


@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    # AWS Configuration
    aws_region: str
    
    # Database Configuration
    aurora_host: str
    aurora_port: int
    aurora_database: str
    aurora_user: str
    aurora_password: str
    
    # DynamoDB Tables
    bookings_table: str
    connections_table: str
    audit_log_table: str
    
    # Bedrock Configuration
    nova_lite_model_id: str
    nova_embeddings_model_id: str
    
    # Authentication
    clerk_secret_key: str
    
    # Environment
    environment: str


def get_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        aws_region=environ.get("AWS_REGION", "us-east-1"),
        aurora_host=environ.get("AURORA_HOST", "localhost"),
        aurora_port=int(environ.get("AURORA_PORT", "5432")),
        aurora_database=environ.get("AURORA_DATABASE", "tripcortex"),
        aurora_user=environ.get("AURORA_USER", "tripcortex"),
        aurora_password=environ.get("AURORA_PASSWORD", "localdev"),
        bookings_table=environ.get("BOOKINGS_TABLE", "Bookings"),
        connections_table=environ.get("CONNECTIONS_TABLE", "Connections"),
        audit_log_table=environ.get("AUDIT_LOG_TABLE", "AuditLog"),
        nova_lite_model_id=environ.get("NOVA_LITE_MODEL_ID", "us.amazon.nova-2-lite-v1:0"),
        nova_embeddings_model_id=environ.get("NOVA_EMBEDDINGS_MODEL_ID", "amazon.nova-2-multimodal-embeddings-v1:0"),
        clerk_secret_key=environ.get("CLERK_SECRET_KEY", ""),
        environment=environ.get("ENVIRONMENT", "local"),
    )
