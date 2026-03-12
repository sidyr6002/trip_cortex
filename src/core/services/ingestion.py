"""Service for managing policy document ingestion via BDA."""

from typing import Any, Literal, cast

from core.db.aurora import AuroraClient
from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import (
    BdaStatusResult,
    IngestionCompleteResult,
    IngestionRequest,
    IngestionStartResult,
)


class IngestionService:
    """Orchestrates BDA invocation, status polling, and policy row management."""

    def __init__(self, bda_runtime_client: Any, aurora_client: AuroraClient) -> None:
        self.bda_runtime_client = bda_runtime_client
        self.aurora_client = aurora_client

    def start_ingestion(
        self, request: IngestionRequest, bda_project_arn: str, output_bucket: str, bda_profile_arn: str = ""
    ) -> IngestionStartResult:
        """
        Start BDA ingestion for a policy document.

        Args:
            request: Ingestion request with S3 URI and file name
            bda_project_arn: ARN of the BDA project
            output_bucket: S3 bucket for BDA output

        Returns:
            IngestionStartResult with policy ID and invocation ARN

        Raises:
            TripCortexError: If BDA API call or DB operation fails
        """
        conn = self.aurora_client._require_connection()

        try:
            # Insert policy row with pending status
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO policies (source_s3_uri, file_name, uploaded_by, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (request.s3_uri, request.file_name, request.uploaded_by, "pending"),
                )
                row = cur.fetchone()
                policy_id = row[0] if row else None
                if not policy_id:
                    raise TripCortexError("Failed to insert policy row", code=ErrorCode.INTERNAL_ERROR)
            conn.commit()

            # Build output S3 URI
            output_s3_uri = f"s3://{output_bucket}/bda-output/{policy_id}/"

            # Invoke BDA
            bda_response = self.bda_runtime_client.invoke_data_automation_async(
                inputConfiguration={"s3Uri": request.s3_uri},
                outputConfiguration={"s3Uri": output_s3_uri},
                dataAutomationConfiguration={
                    "dataAutomationProjectArn": bda_project_arn,
                    "stage": "LIVE",
                },
                dataAutomationProfileArn=bda_profile_arn,
            )
            invocation_arn = bda_response["invocationArn"]

            # Update policy row with processing status and BDA details
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE policies
                    SET status = %s, bda_invocation_arn = %s, bda_project_arn = %s
                    WHERE id = %s
                    """,
                    ("processing", invocation_arn, bda_project_arn, policy_id),
                )
            conn.commit()

            return IngestionStartResult(
                policy_id=str(policy_id),
                invocation_arn=invocation_arn,
                output_s3_uri=output_s3_uri,
            )

        except Exception as e:
            # Mark policy as failed if BDA invocation fails
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE policies
                        SET status = %s, error_message = %s
                        WHERE id = %s
                        """,
                        ("failed", str(e), policy_id),
                    )
                conn.commit()
            except Exception:
                pass  # Ignore cleanup errors

            raise TripCortexError(
                f"Failed to start BDA ingestion: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
            ) from e

    def check_bda_status(self, invocation_arn: str) -> BdaStatusResult:
        """
        Check the status of a BDA ingestion job.

        Args:
            invocation_arn: ARN of the BDA invocation

        Returns:
            BdaStatusResult with current status

        Raises:
            TripCortexError: If BDA API call fails
        """
        try:
            response = self.bda_runtime_client.get_data_automation_status(invocationArn=invocation_arn)

            raw_status = response.get("status", "").upper()
            # BDA returns "INPROGRESS" but our model expects "IN_PROGRESS"
            status = cast(
                Literal["IN_PROGRESS", "SUCCESS", "FAILED"],
                "IN_PROGRESS" if raw_status == "INPROGRESS" else raw_status,
            )
            output_s3_uri = None
            error_message = None

            if status == "SUCCESS":
                output_s3_uri = response.get("outputConfiguration", {}).get("s3Uri")
            elif status == "FAILED":
                error_message = response.get("failureReasons", [{}])[0].get("message")

            return BdaStatusResult(
                invocation_arn=invocation_arn,
                status=status,
                output_s3_uri=output_s3_uri,
                error_message=error_message,
            )

        except Exception as e:
            raise TripCortexError(
                f"Failed to check BDA status: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
            ) from e

    def complete_ingestion(self, policy_id: str, bda_output_s3_uri: str) -> IngestionCompleteResult:
        """
        Mark ingestion as complete and store BDA output location.

        Args:
            policy_id: ID of the policy
            bda_output_s3_uri: S3 URI of BDA output

        Returns:
            IngestionCompleteResult with ready status

        Raises:
            TripCortexError: If DB operation fails
        """
        conn = self.aurora_client._require_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE policies
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    ("ready", policy_id),
                )
            conn.commit()

            return IngestionCompleteResult(
                policy_id=policy_id,
                status="ready",
                bda_output_s3_uri=bda_output_s3_uri,
            )

        except Exception as e:
            raise TripCortexError(
                f"Failed to complete ingestion: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
            ) from e

    def fail_ingestion(self, policy_id: str, error_message: str) -> IngestionCompleteResult:
        """
        Mark ingestion as failed with error message.

        Args:
            policy_id: ID of the policy
            error_message: Error message from BDA

        Returns:
            IngestionCompleteResult with failed status

        Raises:
            TripCortexError: If DB operation fails
        """
        conn = self.aurora_client._require_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE policies
                    SET status = %s, error_message = %s
                    WHERE id = %s
                    """,
                    ("failed", error_message, policy_id),
                )
            conn.commit()

            return IngestionCompleteResult(
                policy_id=policy_id,
                status="failed",
            )

        except Exception as e:
            raise TripCortexError(
                f"Failed to mark ingestion as failed: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
            ) from e
