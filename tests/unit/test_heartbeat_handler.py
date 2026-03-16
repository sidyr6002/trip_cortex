"""Unit tests for WebSocket heartbeat handler."""

from unittest.mock import MagicMock, patch


@patch("handlers.heartbeat.cleanup_stale_bookings")
@patch("handlers.heartbeat.cleanup_stale_connections")
@patch("handlers.heartbeat.get_sfn_client")
@patch("handlers.heartbeat.get_apigw_client")
@patch("handlers.heartbeat.get_dynamo_client")
@patch("handlers.heartbeat.get_config")
def test_heartbeat_calls_both_cleanups(mock_config, mock_dynamo, mock_apigw, mock_sfn, mock_conn, mock_booking):
    from handlers.heartbeat import handler

    mock_config.return_value = MagicMock(connections_table="Connections", bookings_table="Bookings")
    mock_conn.return_value = {"active": 3, "cleaned": 1}
    mock_booking.return_value = {"resolved": 2}

    result = handler({}, None)

    mock_conn.assert_called_once()
    mock_booking.assert_called_once()
    assert result["statusCode"] == 200
    assert "2" in result["body"]  # resolved count in body


@patch("handlers.heartbeat.cleanup_stale_bookings")
@patch("handlers.heartbeat.cleanup_stale_connections")
@patch("handlers.heartbeat.get_sfn_client")
@patch("handlers.heartbeat.get_apigw_client")
@patch("handlers.heartbeat.get_dynamo_client")
@patch("handlers.heartbeat.get_config")
def test_heartbeat_booking_failure_does_not_kill_connection_cleanup(
    mock_config, mock_dynamo, mock_apigw, mock_sfn, mock_conn, mock_booking
):
    from handlers.heartbeat import handler

    mock_config.return_value = MagicMock(connections_table="Connections", bookings_table="Bookings")
    mock_conn.return_value = {"active": 3, "cleaned": 1}
    mock_booking.side_effect = Exception("DynamoDB unavailable")

    # Should propagate — heartbeat itself will fail, but connection cleanup ran first
    try:
        handler({}, None)
    except Exception:
        pass

    mock_conn.assert_called_once()
