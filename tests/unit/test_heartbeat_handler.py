"""Unit tests for WebSocket heartbeat handler."""

from unittest.mock import MagicMock, patch

from handlers.heartbeat import handler


def test_heartbeat_handler():
    with (
        patch("handlers.heartbeat.boto3") as mock_boto3,
        patch("handlers.heartbeat.cleanup_stale_connections") as mock_cleanup,
    ):
        mock_cleanup.return_value = {"active": 3, "cleaned": 1}
        mock_boto3.client.return_value = MagicMock()

        result = handler({}, None)

        assert result["statusCode"] == 200
        mock_cleanup.assert_called_once()
