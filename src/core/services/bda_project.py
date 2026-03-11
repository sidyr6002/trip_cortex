"""Service for managing Bedrock Data Automation projects."""

from typing import Any

from core.errors import ErrorCode, TripCortexError
from core.models.ingestion import BdaProjectResult


class BdaProjectService:
    """Creates or retrieves BDA projects for travel policy document parsing."""

    def __init__(self, bda_client: Any) -> None:
        self.bda_client = bda_client

    def get_or_create_project(self, project_name: str, environment: str) -> BdaProjectResult:
        """
        Get existing BDA project or create a new one.

        Args:
            project_name: Base name for the project
            environment: Environment suffix (dev, staging, prod)

        Returns:
            BdaProjectResult with ARN and status

        Raises:
            TripCortexError: If BDA API call fails
        """
        full_project_name = f"{project_name}-{environment}"

        try:
            # Check if project already exists
            response: dict[str, Any] = self.bda_client.list_data_automation_projects()
            for project in response.get("projects", []):
                if project.get("projectName") == full_project_name:
                    return BdaProjectResult(
                        project_arn=project["projectArn"],
                        project_name=full_project_name,
                        status="existing",
                    )

            # Create new project
            create_response: dict[str, Any] = self.bda_client.create_data_automation_project(
                projectName=full_project_name,
                projectStage="LIVE",
                standardOutputConfiguration=self._build_standard_output_config(),
            )
            return BdaProjectResult(
                project_arn=create_response["projectArn"],
                project_name=full_project_name,
                status="created",
            )
        except Exception as e:
            raise TripCortexError(
                f"Failed to create or retrieve BDA project: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
            ) from e

    def _build_standard_output_config(self) -> dict[str, Any]:
        """Build standard output configuration for BDA project."""
        return {
            "document": {
                "extraction": {
                    "granularity": {
                        "types": ["DOCUMENT", "PAGE", "ELEMENT"]
                    },
                    "boundingBox": {
                        "state": "ENABLED"
                    }
                },
                "generativeField": {
                    "state": "ENABLED"
                },
                "outputFormat": {
                    "textFormat": {
                        "types": ["PLAIN_TEXT", "MARKDOWN"]
                    },
                    "additionalFileFormat": {
                        "state": "ENABLED"
                    }
                }
            }
        }
