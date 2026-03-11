"""Unit tests for IngestionService."""

from unittest.mock import MagicMock

import pytest

from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import (
    BdaStatusResult,
    IngestionCompleteResult,
    IngestionRequest,
    IngestionStartResult,
)
from core.services.ingestion import IngestionService


@pytest.fixture
def mock_bda_client():
    return MagicMock()


@pytest.fixture
def mock_aurora_client():
    client = MagicMock()
    client._require_connection.return_value = MagicMock()
    return client


@pytest.fixture
def service(mock_bda_client, mock_aurora_client):
    return IngestionService(mock_bda_client, mock_aurora_client)


def test_start_ingestion_happy_path(service, mock_bda_client, mock_aurora_client):
    """Test successful ingestion start."""
    # Setup
    policy_id = "550e8400-e29b-41d4-a716-446655440000"
    invocation_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn

    # First cursor call returns policy_id
    mock_cursor.fetchone.return_value = (policy_id,)

    # BDA response
    mock_bda_client.invoke_data_automation_async.return_value = {"invocationArn": invocation_arn}

    # Execute
    request = IngestionRequest(
        s3_uri="s3://bucket/uploads/policy.pdf",
        file_name="policy.pdf",
        uploaded_by="user@example.com",
    )
    result = service.start_ingestion(request, "arn:aws:bedrock:...:project/abc", "bucket")

    # Verify
    assert isinstance(result, IngestionStartResult)
    assert result.policy_id == policy_id
    assert result.invocation_arn == invocation_arn
    assert result.output_s3_uri == f"s3://bucket/bda-output/{policy_id}/"

    # Verify BDA was called with correct args
    call_args = mock_bda_client.invoke_data_automation_async.call_args
    assert call_args[1]["inputConfiguration"]["s3Uri"] == "s3://bucket/uploads/policy.pdf"
    assert call_args[1]["outputConfiguration"]["s3Uri"] == f"s3://bucket/bda-output/{policy_id}/"
    assert call_args[1]["dataAutomationConfiguration"]["stage"] == "LIVE"

    # Verify DB commits
    assert mock_conn.commit.call_count == 2


def test_start_ingestion_bda_api_error(service, mock_bda_client, mock_aurora_client):
    """Test ingestion start handles BDA API errors."""
    policy_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn

    mock_cursor.fetchone.return_value = (policy_id,)
    mock_bda_client.invoke_data_automation_async.side_effect = Exception("BDA API error")

    request = IngestionRequest(
        s3_uri="s3://bucket/uploads/policy.pdf",
        file_name="policy.pdf",
    )

    with pytest.raises(TripCortexError) as exc_info:
        service.start_ingestion(request, "arn:aws:bedrock:...:project/abc", "bucket")

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "Failed to start BDA ingestion" in exc_info.value.message


def test_check_bda_status_in_progress(service, mock_bda_client):
    """Test checking BDA status when job is in progress."""
    invocation_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123"
    mock_bda_client.get_data_automation_status.return_value = {"status": "IN_PROGRESS"}

    result = service.check_bda_status(invocation_arn)

    assert isinstance(result, BdaStatusResult)
    assert result.status == "IN_PROGRESS"
    assert result.output_s3_uri is None
    assert result.error_message is None


def test_check_bda_status_success(service, mock_bda_client):
    """Test checking BDA status when job succeeds."""
    invocation_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123"
    output_uri = "s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/"
    mock_bda_client.get_data_automation_status.return_value = {
        "status": "SUCCESS",
        "outputConfiguration": {"s3Uri": output_uri},
    }

    result = service.check_bda_status(invocation_arn)

    assert result.status == "SUCCESS"
    assert result.output_s3_uri == output_uri
    assert result.error_message is None


def test_check_bda_status_failed(service, mock_bda_client):
    """Test checking BDA status when job fails."""
    invocation_arn = "arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123"
    error_msg = "Document parsing failed: unsupported format"
    mock_bda_client.get_data_automation_status.return_value = {
        "status": "FAILED",
        "failureReasons": [{"message": error_msg}],
    }

    result = service.check_bda_status(invocation_arn)

    assert result.status == "FAILED"
    assert result.error_message == error_msg


def test_check_bda_status_api_error(service, mock_bda_client):
    """Test check_bda_status handles API errors."""
    mock_bda_client.get_data_automation_status.side_effect = Exception("API error")

    with pytest.raises(TripCortexError) as exc_info:
        service.check_bda_status("arn:aws:bedrock:...")

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
    assert "Failed to check BDA status" in exc_info.value.message


def test_complete_ingestion(service, mock_aurora_client):
    """Test completing ingestion."""
    policy_id = "550e8400-e29b-41d4-a716-446655440000"
    output_uri = "s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn

    result = service.complete_ingestion(policy_id, output_uri)

    assert isinstance(result, IngestionCompleteResult)
    assert result.policy_id == policy_id
    assert result.status == "ready"
    assert result.bda_output_s3_uri == output_uri

    # Verify SQL update
    call_args = mock_cursor.execute.call_args
    assert "UPDATE policies" in call_args[0][0]
    assert "ready" in call_args[0][1]
    mock_conn.commit.assert_called_once()


def test_complete_ingestion_db_error(service, mock_aurora_client):
    """Test complete_ingestion handles DB errors."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn
    mock_cursor.execute.side_effect = Exception("DB error")

    with pytest.raises(TripCortexError) as exc_info:
        service.complete_ingestion("policy-id", "s3://bucket/output/")

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR


def test_fail_ingestion(service, mock_aurora_client):
    """Test failing ingestion."""
    policy_id = "550e8400-e29b-41d4-a716-446655440000"
    error_msg = "BDA processing failed"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn

    result = service.fail_ingestion(policy_id, error_msg)

    assert isinstance(result, IngestionCompleteResult)
    assert result.policy_id == policy_id
    assert result.status == "failed"

    # Verify SQL update
    call_args = mock_cursor.execute.call_args
    assert "UPDATE policies" in call_args[0][0]
    assert "failed" in call_args[0][1]
    assert error_msg in call_args[0][1]
    mock_conn.commit.assert_called_once()


def test_fail_ingestion_db_error(service, mock_aurora_client):
    """Test fail_ingestion handles DB errors."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_aurora_client._require_connection.return_value = mock_conn
    mock_cursor.execute.side_effect = Exception("DB error")

    with pytest.raises(TripCortexError) as exc_info:
        service.fail_ingestion("policy-id", "error message")

    assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
