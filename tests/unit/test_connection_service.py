"""Unit tests for connection service."""

from time import time
from unittest.mock import MagicMock

from core.services.connection import delete_connection, store_connection


def test_store_connection():
    mock_client = MagicMock()
    connection_id = "conn-123"
    employee_id = "emp-456"
    table_name = "Connections"

    before_time = int(time()) + 86400
    store_connection(connection_id, employee_id, mock_client, table_name)
    after_time = int(time()) + 86400

    mock_client.put_item.assert_called_once()
    call_args = mock_client.put_item.call_args

    assert call_args.kwargs["TableName"] == table_name
    assert call_args.kwargs["Item"]["connectionId"]["S"] == connection_id
    assert call_args.kwargs["Item"]["employeeId"]["S"] == employee_id

    ttl = int(call_args.kwargs["Item"]["ttl"]["N"])
    assert before_time <= ttl <= after_time


def test_delete_connection():
    mock_client = MagicMock()
    delete_connection("conn-456", mock_client, "Connections")

    mock_client.delete_item.assert_called_once_with(
        TableName="Connections",
        Key={"connectionId": {"S": "conn-456"}},
    )


def test_delete_nonexistent_connection():
    """delete_item is idempotent — no error for missing items."""
    mock_client = MagicMock()
    delete_connection("nonexistent", mock_client, "Connections")
    mock_client.delete_item.assert_called_once()
