"""Unit tests for WebSocket disconnect handler."""

from unittest.mock import MagicMock, patch

from handlers.disconnect import handler


def test_disconnect_handler_deletes_connection():
    event = {"requestContext": {"connectionId": "conn-789"}}

    with (
        patch("handlers.disconnect.get_dynamo_client") as mock_get_client,
        patch("handlers.disconnect.delete_connection") as mock_delete,
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = handler(event, None)

        assert result == {"statusCode": 200}
        mock_delete.assert_called_once_with("conn-789", mock_client, "Connections")


def test_disconnect_handler_returns_200_on_error():
    """Handler must never raise — always returns 200."""
    event = {"requestContext": {"connectionId": "conn-fail"}}

    with (
        patch("handlers.disconnect.get_dynamo_client", return_value=MagicMock()),
        patch("handlers.disconnect.delete_connection", side_effect=Exception("boom")),
    ):
        result = handler(event, None)

        assert result == {"statusCode": 200}
