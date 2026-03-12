"""Lambda handler for S3-triggered ingestion start."""

from typing import Any

from core.clients import get_bda_runtime_client, get_sfn_client
from core.config import get_config
from core.db.aurora import AuroraClient
from core.models.ingestion import IngestionRequest
from core.services.ingestion import IngestionService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Start BDA ingestion when policy PDF is uploaded to S3."""
    config = get_config()

    # Parse event — supports both native S3 notification and EventBridge formats
    if "Records" in event:
        # Native S3 notification format
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
    else:
        # EventBridge format: detail.bucket.name / detail.object.key
        bucket = event["detail"]["bucket"]["name"]
        key = event["detail"]["object"]["key"]

    # Skip non-PDF files
    if not key.endswith(".pdf"):
        return {"status": "skipped", "reason": "not a PDF"}

    # Build ingestion request
    file_name = key.split("/")[-1]
    s3_uri = f"s3://{bucket}/{key}"
    request = IngestionRequest(s3_uri=s3_uri, file_name=file_name)

    # Start ingestion
    aurora_client = AuroraClient(config)
    aurora_client.connect()
    try:
        service = IngestionService(get_bda_runtime_client(), aurora_client)
        result = service.start_ingestion(request, config.bda_project_arn, config.policy_bucket, config.bda_profile_arn)

        # Start Step Functions execution
        sfn_client = get_sfn_client()
        sfn_client.start_execution(
            stateMachineArn=config.ingestion_workflow_arn,
            input=result.model_dump_json(),
        )

        return result.model_dump()
    finally:
        aurora_client.disconnect()
