#!/usr/bin/env python3
"""Create DynamoDB tables for local development.

This script creates the three DynamoDB tables needed for local development and testing, configured
against DynamoDB Local. It matches the SAM template schemas exactly.

Usage:
    python scripts/create_local_tables.py
"""

import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Add src to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import get_config


def create_bookings_table(dynamodb):
    """Create TripCortexBookings table."""
    try:
        dynamodb.create_table(
            TableName="TripCortexBookings",
            KeySchema=[
                {"AttributeName": "employeeId", "KeyType": "HASH"},
                {"AttributeName": "bookingId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "employeeId", "AttributeType": "S"},
                {"AttributeName": "bookingId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("✓ Created TripCortexBookings table")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("✓ TripCortexBookings table already exists")
        else:
            raise


def create_connections_table(dynamodb):
    """Create TripCortexConnections table."""
    try:
        dynamodb.create_table(
            TableName="TripCortexConnections",
            KeySchema=[
                {"AttributeName": "connectionId", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("✓ Created TripCortexConnections table")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("✓ TripCortexConnections table already exists")
        else:
            raise


def create_audit_log_table(dynamodb):
    """Create TripCortexAuditLog table with GSI."""
    try:
        dynamodb.create_table(
            TableName="TripCortexAuditLog",
            KeySchema=[
                {"AttributeName": "bookingId", "KeyType": "HASH"},
                {"AttributeName": "auditId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "bookingId", "AttributeType": "S"},
                {"AttributeName": "auditId", "AttributeType": "S"},
                {"AttributeName": "employeeId", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "employeeId-timestamp-index",
                    "KeySchema": [
                        {"AttributeName": "employeeId", "KeyType": "HASH"},
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("✓ Created TripCortexAuditLog table with GSI")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("✓ TripCortexAuditLog table already exists")
        else:
            raise


def main():
    """Create all DynamoDB tables."""
    config = get_config()
    
    endpoint_url = config.dynamodb_endpoint or "http://localhost:8000"
    
    print(f"Creating DynamoDB tables at {endpoint_url}...")
    print()
    
    # For DynamoDB Local, use dummy credentials
    dynamodb = boto3.client(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=config.aws_region,
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
    
    create_bookings_table(dynamodb)
    create_connections_table(dynamodb)
    create_audit_log_table(dynamodb)
    
    print()
    print("✅ All DynamoDB tables ready")


if __name__ == "__main__":
    main()
