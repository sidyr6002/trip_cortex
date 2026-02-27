"""Unit tests for connection service."""

from time import time
from unittest.mock import MagicMock

from core.services.connection import store_connection


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
