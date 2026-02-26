"""Test that integration test fixtures are working."""

import pytest


@pytest.mark.integration
def test_pg_connection_fixture(pg_connection):
    """Test that PostgreSQL connection fixture works."""
    with pg_connection.cursor() as cur:
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1


@pytest.mark.integration
def test_dynamodb_resource_fixture(dynamodb_resource):
    """Test that DynamoDB resource fixture works."""
    tables = list(dynamodb_resource.tables.all())
    table_names = [table.name for table in tables]
    assert "TripCortexBookings" in table_names
    assert "TripCortexConnections" in table_names
    assert "TripCortexAuditLog" in table_names


@pytest.mark.integration
def test_bookings_table_fixture(bookings_table):
    """Test that bookings table fixture works."""
    assert bookings_table.name == "TripCortexBookings"
    assert bookings_table.key_schema[0]["AttributeName"] == "employeeId"
    assert bookings_table.key_schema[1]["AttributeName"] == "bookingId"


@pytest.mark.integration
def test_connections_table_fixture(connections_table):
    """Test that connections table fixture works."""
    assert connections_table.name == "TripCortexConnections"
    assert connections_table.key_schema[0]["AttributeName"] == "connectionId"


@pytest.mark.integration
def test_audit_log_table_fixture(audit_log_table):
    """Test that audit log table fixture works."""
    assert audit_log_table.name == "TripCortexAuditLog"
    assert audit_log_table.key_schema[0]["AttributeName"] == "bookingId"
    assert audit_log_table.key_schema[1]["AttributeName"] == "auditId"
