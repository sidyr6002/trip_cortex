"""Integration tests for DynamoDB CRUD operations."""

import time
from datetime import datetime, timezone

import pytest


@pytest.mark.integration
def test_put_and_get_booking(bookings_table):
    """Test putting and getting a booking from BookingsTable."""
    # Put a booking
    bookings_table.put_item(
        Item={
            "employeeId": "emp-001",
            "bookingId": "booking-001",
            "status": "confirmed",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    )
    
    # Get the booking
    response = bookings_table.get_item(
        Key={"employeeId": "emp-001", "bookingId": "booking-001"}
    )
    
    assert "Item" in response
    assert response["Item"]["employeeId"] == "emp-001"
    assert response["Item"]["bookingId"] == "booking-001"
    assert response["Item"]["status"] == "confirmed"


@pytest.mark.integration
def test_query_bookings_by_employee(bookings_table):
    """Test querying multiple bookings for the same employee."""
    # Put multiple bookings for the same employee
    bookings_table.put_item(
        Item={
            "employeeId": "emp-002",
            "bookingId": "booking-001",
            "status": "confirmed",
        }
    )
    bookings_table.put_item(
        Item={
            "employeeId": "emp-002",
            "bookingId": "booking-002",
            "status": "pending",
        }
    )
    bookings_table.put_item(
        Item={
            "employeeId": "emp-002",
            "bookingId": "booking-003",
            "status": "cancelled",
        }
    )
    
    # Query by employeeId
    response = bookings_table.query(
        KeyConditionExpression="employeeId = :emp_id",
        ExpressionAttributeValues={":emp_id": "emp-002"},
    )
    
    assert response["Count"] == 3
    booking_ids = [item["bookingId"] for item in response["Items"]]
    assert "booking-001" in booking_ids
    assert "booking-002" in booking_ids
    assert "booking-003" in booking_ids


@pytest.mark.integration
def test_put_and_get_connection(connections_table):
    """Test putting and getting a connection from ConnectionsTable."""
    # Put a connection
    connections_table.put_item(
        Item={
            "connectionId": "conn-001",
            "employeeId": "emp-001",
            "ttl": int(time.time()) + 7200,  # 2 hours from now
        }
    )
    
    # Get the connection
    response = connections_table.get_item(Key={"connectionId": "conn-001"})
    
    assert "Item" in response
    assert response["Item"]["connectionId"] == "conn-001"
    assert response["Item"]["employeeId"] == "emp-001"
    assert "ttl" in response["Item"]


@pytest.mark.integration
def test_delete_connection(connections_table):
    """Test deleting a connection from ConnectionsTable."""
    # Put a connection
    connections_table.put_item(
        Item={"connectionId": "conn-002", "employeeId": "emp-002"}
    )
    
    # Verify it exists
    response = connections_table.get_item(Key={"connectionId": "conn-002"})
    assert "Item" in response
    
    # Delete the connection
    connections_table.delete_item(Key={"connectionId": "conn-002"})
    
    # Verify it's gone
    response = connections_table.get_item(Key={"connectionId": "conn-002"})
    assert "Item" not in response


@pytest.mark.integration
def test_put_and_get_audit_entry(audit_log_table):
    """Test putting and getting an audit entry from AuditLogTable."""
    # Put an audit entry
    audit_log_table.put_item(
        Item={
            "bookingId": "booking-001",
            "auditId": "audit-001",
            "employeeId": "emp-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "policy_check",
            "details": {"result": "approved"},
        }
    )
    
    # Get the audit entry
    response = audit_log_table.get_item(
        Key={"bookingId": "booking-001", "auditId": "audit-001"}
    )
    
    assert "Item" in response
    assert response["Item"]["bookingId"] == "booking-001"
    assert response["Item"]["auditId"] == "audit-001"
    assert response["Item"]["employeeId"] == "emp-001"
    assert response["Item"]["action"] == "policy_check"


@pytest.mark.integration
def test_query_audit_by_employee_gsi(audit_log_table):
    """Test querying audit entries by employee using GSI."""
    # Put multiple audit entries for the same employee
    timestamp1 = "2026-02-26T10:00:00Z"
    timestamp2 = "2026-02-26T11:00:00Z"
    timestamp3 = "2026-02-26T12:00:00Z"
    
    audit_log_table.put_item(
        Item={
            "bookingId": "booking-001",
            "auditId": "audit-001",
            "employeeId": "emp-003",
            "timestamp": timestamp1,
            "action": "policy_check",
        }
    )
    audit_log_table.put_item(
        Item={
            "bookingId": "booking-002",
            "auditId": "audit-002",
            "employeeId": "emp-003",
            "timestamp": timestamp2,
            "action": "flight_search",
        }
    )
    audit_log_table.put_item(
        Item={
            "bookingId": "booking-003",
            "auditId": "audit-003",
            "employeeId": "emp-003",
            "timestamp": timestamp3,
            "action": "booking_confirmed",
        }
    )
    
    # Query by employeeId using GSI
    response = audit_log_table.query(
        IndexName="employeeId-timestamp-index",
        KeyConditionExpression="employeeId = :emp_id",
        ExpressionAttributeValues={":emp_id": "emp-003"},
    )
    
    assert response["Count"] == 3
    actions = [item["action"] for item in response["Items"]]
    assert "policy_check" in actions
    assert "flight_search" in actions
    assert "booking_confirmed" in actions
    
    # Verify items are sorted by timestamp
    timestamps = [item["timestamp"] for item in response["Items"]]
    assert timestamps == sorted(timestamps)
