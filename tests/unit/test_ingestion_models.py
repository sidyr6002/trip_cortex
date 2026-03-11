"""Unit tests for ingestion pipeline models."""

import pytest
from pydantic import ValidationError

from core.models.ingestion import (
    BdaStatusResult,
    IngestionCompleteResult,
    IngestionRequest,
    IngestionStartResult,
)


def test_ingestion_request_valid():
    """Test IngestionRequest construction with valid data."""
    req = IngestionRequest(
        s3_uri="s3://bucket/uploads/policy.pdf",
        file_name="policy.pdf",
        uploaded_by="user@example.com",
    )
    assert req.s3_uri == "s3://bucket/uploads/policy.pdf"
    assert req.file_name == "policy.pdf"
    assert req.uploaded_by == "user@example.com"


def test_ingestion_request_uploaded_by_optional():
    """Test IngestionRequest with uploaded_by omitted."""
    req = IngestionRequest(
        s3_uri="s3://bucket/uploads/policy.pdf",
        file_name="policy.pdf",
    )
    assert req.uploaded_by is None


def test_ingestion_request_missing_required_field():
    """Test IngestionRequest validation fails without required fields."""
    with pytest.raises(ValidationError):
        IngestionRequest(s3_uri="s3://bucket/uploads/policy.pdf")


def test_ingestion_start_result_valid():
    """Test IngestionStartResult construction."""
    result = IngestionStartResult(
        policy_id="550e8400-e29b-41d4-a716-446655440000",
        invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
        output_s3_uri="s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/",
    )
    assert result.policy_id == "550e8400-e29b-41d4-a716-446655440000"
    assert "data-automation-invocation" in result.invocation_arn
    assert result.output_s3_uri.startswith("s3://")


def test_bda_status_result_in_progress():
    """Test BdaStatusResult with IN_PROGRESS status."""
    result = BdaStatusResult(
        invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
        status="IN_PROGRESS",
    )
    assert result.status == "IN_PROGRESS"
    assert result.output_s3_uri is None
    assert result.error_message is None


def test_bda_status_result_success():
    """Test BdaStatusResult with SUCCESS status."""
    result = BdaStatusResult(
        invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
        status="SUCCESS",
        output_s3_uri="s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/",
    )
    assert result.status == "SUCCESS"
    assert result.output_s3_uri is not None


def test_bda_status_result_failed():
    """Test BdaStatusResult with FAILED status."""
    result = BdaStatusResult(
        invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
        status="FAILED",
        error_message="Document parsing failed: unsupported format",
    )
    assert result.status == "FAILED"
    assert result.error_message is not None


def test_bda_status_result_invalid_status():
    """Test BdaStatusResult rejects invalid status."""
    with pytest.raises(ValidationError):
        BdaStatusResult(
            invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
            status="UNKNOWN",
        )


def test_ingestion_complete_result_ready():
    """Test IngestionCompleteResult with ready status."""
    result = IngestionCompleteResult(
        policy_id="550e8400-e29b-41d4-a716-446655440000",
        status="ready",
        total_pages=42,
        bda_output_s3_uri="s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/",
    )
    assert result.status == "ready"
    assert result.total_pages == 42


def test_ingestion_complete_result_failed():
    """Test IngestionCompleteResult with failed status."""
    result = IngestionCompleteResult(
        policy_id="550e8400-e29b-41d4-a716-446655440000",
        status="failed",
    )
    assert result.status == "failed"
    assert result.total_pages is None
    assert result.bda_output_s3_uri is None


def test_ingestion_complete_result_invalid_status():
    """Test IngestionCompleteResult rejects invalid status."""
    with pytest.raises(ValidationError):
        IngestionCompleteResult(
            policy_id="550e8400-e29b-41d4-a716-446655440000",
            status="processing",
        )


def test_models_serialize_to_dict():
    """Test models serialize correctly to dict for Step Functions."""
    result = IngestionStartResult(
        policy_id="550e8400-e29b-41d4-a716-446655440000",
        invocation_arn="arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123",
        output_s3_uri="s3://bucket/bda-output/550e8400-e29b-41d4-a716-446655440000/",
    )
    data = result.model_dump()
    assert isinstance(data, dict)
    assert data["policy_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert data["invocation_arn"] == "arn:aws:bedrock:us-east-1:123456789012:data-automation-invocation/abc123"
