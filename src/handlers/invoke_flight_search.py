"""Lambda handler — invokes ACR flight search workflow."""

from typing import Any

from core.clients import get_acr_client
from core.config import get_config
from core.services.acr_invoke import build_ac_handler_env, invoke_acr_workflow


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    payload = {
        "AC_HANDLER_ENV": build_ac_handler_env(config),
        "booking_id": event["booking_id"],
        "employee_id": event["employee_id"],
        "booking_plan": event["plan"],  # ReasoningResult.plan → FlightSearchInput.booking_plan
    }
    return invoke_acr_workflow(get_acr_client(), config.nova_act_search_agent_arn, payload)
