"""Unit tests for check_bda_status handler."""

from unittest.mock import MagicMock, patch

from core.models.ingestion import BdaStatusResult


@patch("handlers.check_bda_status.get_config")
@patch("handlers.check_bda_status.get_bda_runtime_client")
@patch("handlers.check_bda_status.AuroraClient")
@patch("handlers.check_bda_status.IngestionService")
def test_check_bda_status_handler(mock_svc_class, mock_aurora_class, mock_get_bda, mock_get_config):
    """invocation_arn passed through correctly, result returned."""
    from handlers.check_bda_status import handler

    mock_get_config.return_value = MagicMock()
    mock_svc_class.return_value.check_bda_status.return_value = BdaStatusResult(
        invocation_arn="arn:aws:bedrock:...", status="IN_PROGRESS"
    )

    result = handler({"invocation_arn": "arn:aws:bedrock:..."}, {})

    assert result["status"] == "IN_PROGRESS"
    mock_svc_class.return_value.check_bda_status.assert_called_once_with("arn:aws:bedrock:...")
