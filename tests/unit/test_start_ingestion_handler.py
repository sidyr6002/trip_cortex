"""Unit tests for start_ingestion handler."""

from unittest.mock import MagicMock, patch

import pytest

from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import IngestionStartResult

S3_EVENT = {
    "Records": [
        {
            "s3": {
                "bucket": {"name": "trip-cortex-policy-docs-123456789012"},
                "object": {"key": "uploads/policy.pdf"},
            }
        }
    ]
}


@patch("handlers.start_ingestion.get_config")
@patch("handlers.start_ingestion.get_bda_runtime_client")
@patch("handlers.start_ingestion.get_sfn_client")
@patch("handlers.start_ingestion.AuroraClient")
@patch("handlers.start_ingestion.IngestionService")
def test_start_ingestion_happy_path(mock_svc_class, mock_aurora_class, mock_get_sfn, mock_get_bda, mock_get_config):
    """S3 event parsed correctly, service called, SFN started."""
    from handlers.start_ingestion import handler

    mock_config = MagicMock()
    mock_config.bda_project_arn = "arn:aws:bedrock:..."
    mock_config.policy_bucket = "bucket"
    mock_config.ingestion_workflow_arn = "arn:aws:states:..."
    mock_get_config.return_value = mock_config

    mock_sfn = MagicMock()
    mock_get_sfn.return_value = mock_sfn
    mock_svc_class.return_value.start_ingestion.return_value = IngestionStartResult(
        policy_id="policy-id",
        invocation_arn="arn:aws:bedrock:...",
        output_s3_uri="s3://bucket/bda-output/policy-id/",
    )

    result = handler(S3_EVENT, {})

    assert result["policy_id"] == "policy-id"
    call_request = mock_svc_class.return_value.start_ingestion.call_args[0][0]
    assert call_request.s3_uri == "s3://trip-cortex-policy-docs-123456789012/uploads/policy.pdf"
    assert call_request.file_name == "policy.pdf"
    mock_sfn.start_execution.assert_called_once()


@patch("handlers.start_ingestion.get_config")
@patch("handlers.start_ingestion.AuroraClient")
def test_start_ingestion_non_pdf_skipped(mock_aurora_class, mock_get_config):
    """Non-PDF key returns early without calling service."""
    from handlers.start_ingestion import handler

    mock_get_config.return_value = MagicMock()
    event = {"Records": [{"s3": {"bucket": {"name": "bucket"}, "object": {"key": "uploads/policy.txt"}}}]}

    result = handler(event, {})

    assert result["status"] == "skipped"
    mock_aurora_class.assert_not_called()


@patch("handlers.start_ingestion.get_config")
@patch("handlers.start_ingestion.get_bda_runtime_client")
@patch("handlers.start_ingestion.get_sfn_client")
@patch("handlers.start_ingestion.AuroraClient")
@patch("handlers.start_ingestion.IngestionService")
def test_start_ingestion_service_error_propagates(
    mock_svc_class, mock_aurora_class, mock_get_sfn, mock_get_bda, mock_get_config
):
    """Service errors propagate out of the handler."""
    from handlers.start_ingestion import handler

    mock_get_config.return_value = MagicMock()
    mock_svc_class.return_value.start_ingestion.side_effect = TripCortexError(
        "BDA failed", code=ErrorCode.INTERNAL_ERROR
    )

    with pytest.raises(TripCortexError):
        handler(S3_EVENT, {})
