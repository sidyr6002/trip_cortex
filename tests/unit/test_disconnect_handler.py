"""Unit tests for WebSocket disconnect handler."""

from unittest.mock import MagicMock, patch

from handlers.disconnect import handler


def test_disconnect_handler_deletes_connection():
    event = {"requestContext": {"connectionId": "conn-789"}}

    with patch("handlers.disconnect.boto3") as mock_boto3, \
         patch("handlers.disconnect.delete_connection") as mock_delete:
        mock_boto3.client.return_value = MagicMock()

        result = handler(event, None)

        assert result == {"statusCode": 200}
        mock_delete.assert_called_once_with("conn-789", mock_boto3.client.return_value, "Connections")


def test_disconnect_handler_returns_200_on_error():
    """Handler must never raise — always returns 200."""
    event = {"requestContext": {"connectionId": "conn-fail"}}

    with patch("handlers.disconnect.boto3"), \
         patch("handlers.disconnect.delete_connection", side_effect=Exception("boom")):
        result = handler(event, None)

        assert result == {"statusCode": 200}
