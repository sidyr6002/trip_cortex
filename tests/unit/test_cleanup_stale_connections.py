"""Unit tests for cleanup_stale_connections service."""

from unittest.mock import MagicMock, patch

from core.services.connection import cleanup_stale_connections


def test_cleanup_pings_active_and_removes_stale():
    dynamo = MagicMock()
    apigw = MagicMock()

    dynamo.scan.return_value = {
        "Items": [
            {"connectionId": {"S": "conn-active"}},
            {"connectionId": {"S": "conn-stale"}},
        ]
    }

    gone_exc = type("GoneException", (Exception,), {})
    apigw.exceptions.GoneException = gone_exc
    apigw.post_to_connection.side_effect = [None, gone_exc()]

    with patch("core.services.connection.delete_connection") as mock_delete:
        result = cleanup_stale_connections(dynamo, apigw, "Connections")

    assert result == {"active": 1, "cleaned": 1}
    mock_delete.assert_called_once_with("conn-stale", dynamo, "Connections")


def test_cleanup_handles_pagination():
    dynamo = MagicMock()
    apigw = MagicMock()
    apigw.exceptions.GoneException = type("GoneException", (Exception,), {})

    dynamo.scan.side_effect = [
        {
            "Items": [{"connectionId": {"S": "conn-1"}}],
            "LastEvaluatedKey": {"connectionId": {"S": "conn-1"}},
        },
        {
            "Items": [{"connectionId": {"S": "conn-2"}}],
        },
    ]

    result = cleanup_stale_connections(dynamo, apigw, "Connections")

    assert result == {"active": 2, "cleaned": 0}
    assert dynamo.scan.call_count == 2


def test_cleanup_empty_table():
    dynamo = MagicMock()
    apigw = MagicMock()
    apigw.exceptions.GoneException = type("GoneException", (Exception,), {})

    dynamo.scan.return_value = {"Items": []}

    result = cleanup_stale_connections(dynamo, apigw, "Connections")

    assert result == {"active": 0, "cleaned": 0}
