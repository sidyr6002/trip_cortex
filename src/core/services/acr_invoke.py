"""ACR invocation service — wraps bedrock-agentcore invoke_agent_runtime."""

import json
from typing import Any

from core.config import Config


def invoke_acr_workflow(client: Any, agent_runtime_arn: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke an ACR-deployed Nova Act workflow and return the parsed response."""
    resp = client.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        qualifier="DEFAULT",
        payload=json.dumps(payload).encode(),
        contentType="application/json",
        accept="application/json",
    )
    result: dict[str, Any] = json.loads(resp["response"].read().decode())
    return result


def build_ac_handler_env(config: Config) -> dict[str, str]:
    """Build the AC_HANDLER_ENV block injected into ACR payload as runtime env vars."""
    return {
        "DUMMY_PORTAL_URL": config.dummy_portal_url,
        "NOVA_ACT_SEARCH_WORKFLOW": config.nova_act_search_workflow,
        "NOVA_ACT_BOOKING_WORKFLOW": config.nova_act_booking_workflow,
        "NOVA_ACT_HEADLESS": str(config.nova_act_headless).lower(),
        "PORTAL_TEST_EMAIL": config.portal_test_email,
        "PORTAL_TEST_PASSWORD": config.portal_test_password,
        "AUDIT_LOG_TABLE": config.audit_log_table,
    }
