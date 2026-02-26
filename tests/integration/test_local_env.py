"""End-to-end smoke test for local development environment."""

import uuid

import pytest
from psycopg.types.json import Json


@pytest.mark.integration
def test_full_local_environment(pg_connection, bookings_table):
    """Test complete local environment setup with both databases."""
    # Test 1: Verify PostgreSQL connection and pgvector extension
    with pg_connection.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        assert cur.fetchone()[0] == "vector"
    
    # Test 2: Verify all 3 DynamoDB tables exist and are ACTIVE
    dynamodb_client = bookings_table.meta.client
    
    tables_response = dynamodb_client.list_tables()
    table_names = tables_response["TableNames"]
    assert "TripCortexBookings" in table_names
    assert "TripCortexConnections" in table_names
    assert "TripCortexAuditLog" in table_names
    
    # Verify tables are ACTIVE
    for table_name in ["TripCortexBookings", "TripCortexConnections", "TripCortexAuditLog"]:
        table_desc = dynamodb_client.describe_table(TableName=table_name)
        assert table_desc["Table"]["TableStatus"] == "ACTIVE"
    
    # Test 3: Insert a policy chunk with embedding into PostgreSQL
    policy_id = uuid.uuid4()
    chunk_id = None
    
    # Create a test vector
    test_vector = [0.5] * 1024
    vector_str = "[" + ",".join(str(v) for v in test_vector) + "]"
    
    with pg_connection.cursor() as cur:
        cur.execute("""
            INSERT INTO policy_chunks 
            (policy_id, content_type, content_text, embedding, metadata)
            VALUES (%s, %s, %s, %s::vector, %s)
            RETURNING id
        """, (
            policy_id,
            "text",
            "Test policy: Book flights 7 days in advance",
            vector_str,
            Json({"test": True, "environment": "local"})
        ))
        chunk_id = cur.fetchone()[0]
        pg_connection.commit()
    
    # Test 4: Insert a booking record into DynamoDB
    booking_id = str(uuid.uuid4())
    employee_id = "emp-test-001"
    
    bookings_table.put_item(
        Item={
            "employeeId": employee_id,
            "bookingId": booking_id,
            "status": "confirmed",
            "policyId": str(policy_id),
            "testData": True,
        }
    )
    
    # Test 5: Query both back successfully
    # Query PostgreSQL
    with pg_connection.cursor() as cur:
        cur.execute("""
            SELECT id, policy_id, content_type, content_text, metadata
            FROM policy_chunks
            WHERE id = %s
        """, (chunk_id,))
        pg_result = cur.fetchone()
        
        assert pg_result is not None
        assert pg_result[0] == chunk_id
        assert pg_result[1] == policy_id
        assert pg_result[2] == "text"
        assert "7 days in advance" in pg_result[3]
        assert pg_result[4]["test"] is True
        assert pg_result[4]["environment"] == "local"
    
    # Query DynamoDB
    dynamo_response = bookings_table.get_item(
        Key={"employeeId": employee_id, "bookingId": booking_id}
    )
    
    assert "Item" in dynamo_response
    assert dynamo_response["Item"]["employeeId"] == employee_id
    assert dynamo_response["Item"]["bookingId"] == booking_id
    assert dynamo_response["Item"]["status"] == "confirmed"
    assert dynamo_response["Item"]["policyId"] == str(policy_id)
    
    # Test 6: Verify cross-database relationship
    # The booking references the policy via policyId
    assert dynamo_response["Item"]["policyId"] == str(policy_id)
    
    # Test 7: Clean up
    with pg_connection.cursor() as cur:
        cur.execute("DELETE FROM policy_chunks WHERE id = %s", (chunk_id,))
        pg_connection.commit()
    
    bookings_table.delete_item(
        Key={"employeeId": employee_id, "bookingId": booking_id}
    )
    
    # Verify cleanup
    with pg_connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM policy_chunks WHERE id = %s", (chunk_id,))
        assert cur.fetchone()[0] == 0
    
    cleanup_response = bookings_table.get_item(
        Key={"employeeId": employee_id, "bookingId": booking_id}
    )
    assert "Item" not in cleanup_response
