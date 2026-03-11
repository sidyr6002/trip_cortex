"""Unit tests for BdaProjectService."""

from unittest.mock import MagicMock

import pytest

from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import BdaProjectResult
from core.services.bda_project import BdaProjectService


@pytest.fixture
def mock_bda_client():
    return MagicMock()


@pytest.fixture
def service(mock_bda_client):
    return BdaProjectService(mock_bda_client)


def test_get_or_create_project_existing(service, mock_bda_client):
    """Test retrieving an existing project returns status 'existing'."""
    existing_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/travel-policy-processor-dev"
    mock_bda_client.list_data_automation_projects.return_value = {
        "projects": [{"projectName": "travel-policy-processor-dev", "projectArn": existing_arn}]
    }

    result = service.get_or_create_project("travel-policy-processor", "dev")

    assert isinstance(result, BdaProjectResult)
    assert result.project_arn == existing_arn
    assert result.status == "existing"
    mock_bda_client.create_data_automation_project.assert_not_called()


def test_get_or_create_project_new(service, mock_bda_client):
    """Test creating a new project returns status 'created'."""
    new_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/travel-policy-processor-dev"
    mock_bda_client.list_data_automation_projects.return_value = {"projects": []}
    mock_bda_client.create_data_automation_project.return_value = {"projectArn": new_arn}

    result = service.get_or_create_project("travel-policy-processor", "dev")

    assert isinstance(result, BdaProjectResult)
    assert result.project_arn == new_arn
    assert result.status == "created"
    mock_bda_client.create_data_automation_project.assert_called_once()


def test_get_or_create_project_correct_config(service, mock_bda_client):
    """Test that correct standardOutputConfiguration is passed to create_data_automation_project."""
    new_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/travel-policy-processor-dev"
    mock_bda_client.list_data_automation_projects.return_value = {"projects": []}
    mock_bda_client.create_data_automation_project.return_value = {"projectArn": new_arn}

    service.get_or_create_project("travel-policy-processor", "dev")

    call_args = mock_bda_client.create_data_automation_project.call_args
    assert call_args[1]["projectName"] == "travel-policy-processor-dev"
    assert call_args[1]["projectStage"] == "LIVE"

    config = call_args[1]["standardOutputConfiguration"]
    assert config["document"]["extraction"]["granularity"]["types"] == [
        "DOCUMENT",
        "PAGE",
        "ELEMENT",
    ]
    assert config["document"]["extraction"]["boundingBox"]["state"] == "ENABLED"
    assert config["document"]["generativeField"]["state"] == "ENABLED"
    assert config["document"]["outputFormat"]["textFormat"]["types"] == [
        "PLAIN_TEXT",
        "MARKDOWN",
    ]
    assert config["document"]["outputFormat"]["additionalFileFormat"]["state"] == "ENABLED"


def test_get_or_create_project_api_error(service, mock_bda_client):
    """Test that API errors are wrapped in TripCortexError."""
    mock_bda_client.list_data_automation_projects.side_effect = Exception("BDA API error")

    with pytest.raises(TripCortexError) as exc_info:
        service.get_or_create_project("travel-policy-processor", "dev")

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "Failed to create or retrieve BDA project" in exc_info.value.message


def test_get_or_create_project_environment_suffix(service, mock_bda_client):
    """Test that project name includes environment suffix."""
    existing_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-project/travel-policy-processor-staging"
    mock_bda_client.list_data_automation_projects.return_value = {
        "projects": [{"projectName": "travel-policy-processor-staging", "projectArn": existing_arn}]
    }

    result = service.get_or_create_project("travel-policy-processor", "staging")

    assert result.project_arn == existing_arn
    assert result.project_name == "travel-policy-processor-staging"
