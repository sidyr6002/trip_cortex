"""Shared test fixtures for Trip Cortex."""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load .env file for test configuration
load_dotenv()

# Unset AWS_PROFILE for local testing (DynamoDB Local doesn't need it)
if "AWS_PROFILE" in os.environ:
    del os.environ["AWS_PROFILE"]

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# PostgreSQL fixtures
@pytest.fixture
def pg_connection():
    """Provide a PostgreSQL connection for integration tests."""
    import psycopg
    from core.config import get_config
    
    config = get_config()
    conn_str = (
        f"host={config.aurora_host} port={config.aurora_port} "
        f"dbname={config.aurora_database} user={config.aurora_user} "
        f"password={config.aurora_password}"
    )
    
    conn = psycopg.connect(conn_str)
    yield conn
    
    # Rollback any uncommitted changes
    conn.rollback()
    conn.close()


# DynamoDB fixtures
@pytest.fixture
def dynamodb_resource():
    """Provide a DynamoDB resource for integration tests."""
    import boto3
    from core.config import get_config
    
    config = get_config()
    
    resource = boto3.resource(
        "dynamodb",
        endpoint_url=config.dynamodb_endpoint,
        region_name=config.aws_region,
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
    
    return resource


@pytest.fixture
def bookings_table(dynamodb_resource):
    """Provide the TripCortexBookings table."""
    table = dynamodb_resource.Table("TripCortexBookings")
    yield table
    
    # Cleanup: scan and delete all items created during test
    response = table.scan()
    with table.batch_writer() as batch:
        for item in response.get("Items", []):
            batch.delete_item(
                Key={
                    "employeeId": item["employeeId"],
                    "bookingId": item["bookingId"],
                }
            )


@pytest.fixture
def connections_table(dynamodb_resource):
    """Provide the TripCortexConnections table."""
    table = dynamodb_resource.Table("TripCortexConnections")
    yield table
    
    # Cleanup: scan and delete all items created during test
    response = table.scan()
    with table.batch_writer() as batch:
        for item in response.get("Items", []):
            batch.delete_item(Key={"connectionId": item["connectionId"]})


@pytest.fixture
def audit_log_table(dynamodb_resource):
    """Provide the TripCortexAuditLog table."""
    table = dynamodb_resource.Table("TripCortexAuditLog")
    yield table
    
    # Cleanup: scan and delete all items created during test
    response = table.scan()
    with table.batch_writer() as batch:
        for item in response.get("Items", []):
            batch.delete_item(
                Key={
                    "bookingId": item["bookingId"],
                    "auditId": item["auditId"],
                }
            )
