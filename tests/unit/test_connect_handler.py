"""Unit tests for WebSocket connect handler."""

from unittest.mock import MagicMock, patch

from handlers.connect import handler


def test_connect_handler():
    event = {
        "requestContext": {
            "connectionId": "conn-abc123",
            "authorizer": {"employeeId": "emp-xyz789"},
        }
    }

    with patch("handlers.connect.boto3") as mock_boto3, patch("handlers.connect.store_connection") as mock_store:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        result = handler(event, None)

        assert result == {"statusCode": 200}
        mock_store.assert_called_once_with("conn-abc123", "emp-xyz789", mock_client, "Connections")
