"""Lambda handler — invokes ACR flight booking workflow."""

from typing import Any

from core.clients import get_acr_client
from core.config import get_config
from core.services.acr_invoke import build_ac_handler_env, invoke_acr_workflow


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    # event contains the HITL resume output merged with preserved workflow state
    payload = {
        "AC_HANDLER_ENV": build_ac_handler_env(config),
        "booking_id": event["booking_id"],
        "employee_id": event["employee_id"],
        "flight": event["selected_flight"]["flight"],
        "booking_plan": event["validated_result"]["plan"],
        "passengers": event["selected_flight"]["passengers"],
        "search_url": event["selected_flight"]["search_url"],
    }
    return invoke_acr_workflow(get_acr_client(), config.nova_act_booking_agent_arn, payload)
