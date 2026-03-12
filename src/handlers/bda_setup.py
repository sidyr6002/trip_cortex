"""Lambda handler for one-time BDA project setup."""

from typing import Any

import boto3

from core.clients import get_bda_client
from core.config import get_config
from core.services.bda_project import BdaProjectService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Create or retrieve BDA project and store ARN in SSM Parameter Store."""
    config = get_config()

    service = BdaProjectService(get_bda_client())
    result = service.get_or_create_project(
        project_name="travel-policy-processor",
        environment=config.environment,
    )

    ssm_client = boto3.client("ssm", region_name=config.aws_region)
    ssm_client.put_parameter(
        Name=f"/trip-cortex/{config.environment}/bda-project-arn",
        Value=result.project_arn,
        Type="String",
        Overwrite=True,
    )

    return result.model_dump()
