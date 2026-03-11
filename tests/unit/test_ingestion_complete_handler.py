"""Unit tests for ingestion_complete handler."""

from unittest.mock import MagicMock, patch

from core.models.ingestion import IngestionCompleteResult


@patch("handlers.ingestion_complete.get_config")
@patch("handlers.ingestion_complete.get_bda_runtime_client")
@patch("handlers.ingestion_complete.AuroraClient")
@patch("handlers.ingestion_complete.IngestionService")
def test_ingestion_complete_handler(mock_svc_class, mock_aurora_class, mock_get_bda, mock_get_config):
    """policy_id and output_s3_uri passed through correctly."""
    from handlers.ingestion_complete import handler

    mock_get_config.return_value = MagicMock()
    mock_svc_class.return_value.complete_ingestion.return_value = IngestionCompleteResult(
        policy_id="policy-id",
        status="ready",
        bda_output_s3_uri="s3://bucket/bda-output/policy-id/",
    )

    result = handler({"policy_id": "policy-id", "output_s3_uri": "s3://bucket/bda-output/policy-id/"}, {})

    assert result["status"] == "ready"
    mock_svc_class.return_value.complete_ingestion.assert_called_once_with(
        "policy-id", "s3://bucket/bda-output/policy-id/"
    )
