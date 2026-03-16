"""Quick HITL approval smoke test — sends approval email to user."""
import base64, os
from pathlib import Path
from amzn_nova_act_human_intervention_client import (
    ApprovalInterventionExecutor,
    ApprovalRequest,
    AssumedRoleCredentialsProvider,
    InterventionContext,
)
from amzn_nova_act_human_intervention_common import (
    ApprovalAction,
    ApprovalOption,
    EmailContactInfo,
    NotificationRecipient,
)
import boto3

ENDPOINT = "wss://pqp21wvq49.execute-api.us-east-1.amazonaws.com/dev"
ROLE_ARN = "arn:aws:iam::591618107284:role/NovaAct-HITL-ExecutionRole-trip-cortex"
BUCKET = "nova-act-hitl-most-recent-screenshots-591618107284-trip-cortex"
EMAIL = "siddhardhrahul@gmail.com"

# Use the test screenshot from samples
screenshot_path = Path(__file__).parent.parent / "nova-act-human-intervention/samples/test_screenshot.png"
with open(screenshot_path, "rb") as f:
    screenshot_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

creds = AssumedRoleCredentialsProvider(
    role_arn=ROLE_ARN, duration_seconds=900, session=boto3.Session(region_name="us-east-1"),
)

executor = ApprovalInterventionExecutor(
    endpoint=ENDPOINT, intervention_context=InterventionContext(
        workflow_run_id="smoke-test-001", act_session_id="smoke-session", act_id="smoke-act",
    ),
    screenshot_s3_bucket=BUCKET, credentials_provider=creds, region="us-east-1", execution_timeout=900,
)

print("Sending approval request...")
result = executor.execute(ApprovalRequest(
    notification_recipients=[
        NotificationRecipient(contact_info=EmailContactInfo(
            to_email_address=EMAIL, from_email_address=EMAIL,
        ))
    ],
    timeout=600,
    question="Approve payment of $95.20 for flight 6E-2134 DEL→BOM?",
    options=[
        ApprovalOption(label="Approve", action=ApprovalAction.APPROVE),
        ApprovalOption(label="Deny", action=ApprovalAction.DENY),
    ],
    most_recent_screenshot=screenshot_b64,
))
print(f"Result: {result}")
