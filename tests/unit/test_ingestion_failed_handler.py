"""Unit tests for ingestion_failed handler."""

from unittest.mock import MagicMock, patch

from core.models.ingestion import IngestionCompleteResult


@patch("handlers.ingestion_failed.get_config")
@patch("handlers.ingestion_failed.get_bda_runtime_client")
@patch("handlers.ingestion_failed.AuroraClient")
@patch("handlers.ingestion_failed.IngestionService")
def test_ingestion_failed_handler(mock_svc_class, mock_aurora_class, mock_get_bda, mock_get_config):
    """policy_id and error_message passed through correctly."""
    from handlers.ingestion_failed import handler

    mock_get_config.return_value = MagicMock()
    mock_svc_class.return_value.fail_ingestion.return_value = IngestionCompleteResult(
        policy_id="policy-id", status="failed"
    )

    result = handler({"policy_id": "policy-id", "error_message": "BDA failed"}, {})

    assert result["status"] == "failed"
    mock_svc_class.return_value.fail_ingestion.assert_called_once_with("policy-id", "BDA failed")


@patch("handlers.ingestion_failed.get_config")
@patch("handlers.ingestion_failed.get_bda_runtime_client")
@patch("handlers.ingestion_failed.AuroraClient")
@patch("handlers.ingestion_failed.IngestionService")
def test_ingestion_failed_db_error_swallowed(mock_svc_class, mock_aurora_class, mock_get_bda, mock_get_config):
    """DB failure is logged but not re-raised."""
    from handlers.ingestion_failed import handler

    mock_get_config.return_value = MagicMock()
    mock_svc_class.return_value.fail_ingestion.side_effect = Exception("DB error")

    result = handler({"policy_id": "policy-id", "error_message": "BDA failed"}, {})

    assert result["policy_id"] == "policy-id"
    assert result["status"] == "failed"
    assert "error" in result
