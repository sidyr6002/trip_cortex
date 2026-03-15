"""Lambda handler — invokes ACR flight booking workflow."""

from typing import Any

from core.clients import get_acr_client, get_circuit_breaker_service, get_dynamo_client
from core.config import get_config
from core.errors import PortalUnavailableError
from core.services.acr_invoke import build_ac_handler_env, invoke_acr_workflow
from core.services.audit import build_circuit_breaker_audit_entry, write_audit_log

_CIRCUIT_ID = "travel-portal-booking"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = get_config()
    cb = get_circuit_breaker_service(failure_threshold=3, recovery_timeout=60)

    if not cb.can_execute(_CIRCUIT_ID):
        write_audit_log(
            get_dynamo_client(),
            config.audit_log_table,
            build_circuit_breaker_audit_entry(
                event["booking_id"], event["employee_id"], _CIRCUIT_ID, "rejected", 0
            ),
        )
        raise PortalUnavailableError("Circuit breaker OPEN for travel-portal-booking")

    payload = {
        "AC_HANDLER_ENV": build_ac_handler_env(config),
        "booking_id": event["booking_id"],
        "employee_id": event["employee_id"],
        "flight": event["selected_flight"]["flight"],
        "booking_plan": event["validated_result"]["plan"],
        "passengers": event["selected_flight"]["passengers"],
        "search_url": event["selected_flight"]["search_url"],
    }
    try:
        result = invoke_acr_workflow(get_acr_client(), config.nova_act_booking_agent_arn, payload)
        state = cb.record_success(_CIRCUIT_ID)
        if state.failure_count == 0 and state.state.value == "closed":
            write_audit_log(
                get_dynamo_client(),
                config.audit_log_table,
                build_circuit_breaker_audit_entry(
                    event["booking_id"], event["employee_id"], _CIRCUIT_ID, "closed", 0
                ),
            )
        return result
    except Exception:
        state = cb.record_failure(_CIRCUIT_ID)
        if state.state.value == "open":
            write_audit_log(
                get_dynamo_client(),
                config.audit_log_table,
                build_circuit_breaker_audit_entry(
                    event["booking_id"], event["employee_id"], _CIRCUIT_ID, "opened", state.failure_count
                ),
            )
        raise
