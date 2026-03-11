"""Unit tests for bda_setup handler."""

from unittest.mock import MagicMock, patch

import pytest

from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import BdaProjectResult


@patch("handlers.bda_setup.get_config")
@patch("handlers.bda_setup.get_bda_client")
@patch("handlers.bda_setup.BdaProjectService")
@patch("handlers.bda_setup.boto3.client")
def test_bda_setup_handler_success(mock_boto3_client, mock_service_class, mock_get_bda_client, mock_get_config):
    """Test handler happy path."""
    from handlers.bda_setup import handler

    mock_config = MagicMock()
    mock_config.environment = "dev"
    mock_config.aws_region = "us-east-1"
    mock_get_config.return_value = mock_config

    mock_get_bda_client.return_value = MagicMock()

    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    project_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/travel-policy-processor-dev"
    mock_service.get_or_create_project.return_value = BdaProjectResult(
        project_arn=project_arn,
        project_name="travel-policy-processor-dev",
        status="created",
    )

    mock_ssm_client = MagicMock()
    mock_boto3_client.return_value = mock_ssm_client

    result = handler({}, {})

    assert result["project_arn"] == project_arn
    assert result["status"] == "created"
    mock_ssm_client.put_parameter.assert_called_once_with(
        Name="/trip-cortex/dev/bda-project-arn",
        Value=project_arn,
        Type="String",
        Overwrite=True,
    )


@patch("handlers.bda_setup.get_config")
@patch("handlers.bda_setup.get_bda_client")
@patch("handlers.bda_setup.BdaProjectService")
def test_bda_setup_handler_service_error(mock_service_class, mock_get_bda_client, mock_get_config):
    """Test handler propagates service errors."""
    from handlers.bda_setup import handler

    mock_config = MagicMock()
    mock_config.environment = "dev"
    mock_get_config.return_value = mock_config
    mock_get_bda_client.return_value = MagicMock()

    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.get_or_create_project.side_effect = TripCortexError("BDA API failed", code=ErrorCode.INTERNAL_ERROR)

    with pytest.raises(TripCortexError):
        handler({}, {})
