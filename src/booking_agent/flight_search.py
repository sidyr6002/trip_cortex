"""
Flight search Nova Act workflow script for FlySmart dummy portal.

Local dev:
    PYTHONPATH=src .venv/bin/python src/booking_agent/flight_search.py

ACR entry point: main(payload) — called by agentcore_handler.py
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import boto3
import structlog
from nova_act import (
    ActExceededMaxStepsError,
    ActGuardrailsError,
    ActRateLimitExceededError,
    ActStateGuardrailError,
    ActTimeoutError,
    NovaAct,
    Workflow,
)

try:
    from booking_agent.config import nova_act_kwargs, workflow_kwargs  # PYTHONPATH=src (local/test)
except ModuleNotFoundError:
    from config import nova_act_kwargs, workflow_kwargs  # type: ignore[no-redef]  # ACR flat layout
from core.config import get_config
from core.models.flight import FlightSearchInput, FlightSearchOutput, FlightSearchResult
from core.services.audit import build_flight_search_audit_entry, build_recovery_audit_entry, write_audit_log
from core.services.error_classification import RecoveryStrategy, classify_nova_act_error
from core.services.flight_search import (
    build_fallback_url,
    build_filter_prompt,
    build_search_url,
    filter_by_constraints,
)
from core.services.nova_act_recovery import reorient, should_retry

log = structlog.get_logger()

_EXTRACT_PROMPT = (
    "Extract all available (not sold out) flight options from the search results. "
    "For each flight include: airline name, flight number, price in USD (numeric only), "
    "departure time, arrival time, number of stops (0 for Direct), cabin class, and duration."
)


def _run(nova: NovaAct, inp: FlightSearchInput, base_url: str, *, allow_reorient: bool = True) -> FlightSearchOutput:
    constraints = inp.booking_plan.policy_constraints
    warnings: list[str] = []
    search_url = build_search_url(inp.booking_plan, base_url)

    filter_prompt = build_filter_prompt(constraints)
    if filter_prompt:
        nova.act(filter_prompt)

    try:
        result = nova.act_get(_EXTRACT_PROMPT, schema=FlightSearchResult.model_json_schema(), max_steps=50)
    except ActExceededMaxStepsError:
        if allow_reorient and reorient(nova, _EXTRACT_PROMPT, search_url):
            return _run(nova, inp, base_url, allow_reorient=False)
        raise

    flights = FlightSearchResult.model_validate(result.parsed_response)

    if not flights.flights:
        warnings.append("ALL_FLIGHTS_SOLD_OUT")
        return FlightSearchOutput(
            booking_id=inp.booking_id,
            employee_id=inp.employee_id,
            search_result=flights,
            fallback_url=build_fallback_url(inp.booking_plan, base_url),
            warnings=warnings,
        )

    flights, filter_warnings = filter_by_constraints(flights, constraints)
    warnings.extend(filter_warnings)

    fallback = build_fallback_url(inp.booking_plan, base_url) if filter_warnings else None
    return FlightSearchOutput(
        booking_id=inp.booking_id,
        employee_id=inp.employee_id,
        search_result=flights,
        fallback_url=fallback,
        warnings=warnings,
    )


def _error_output(inp: FlightSearchInput, base_url: str, warning: str) -> FlightSearchOutput:
    p = inp.booking_plan.parameters
    return FlightSearchOutput(
        booking_id=inp.booking_id,
        employee_id=inp.employee_id,
        search_result=FlightSearchResult(
            flights=[],
            search_origin=p.origin,
            search_destination=p.destination,
            search_date=p.departure_date.isoformat(),
            total_results=0,
        ),
        fallback_url=build_fallback_url(inp.booking_plan, base_url, warning),
        warnings=[warning],
    )


def main(payload: dict) -> dict:
    """Entry point for both local dev and ACR (agentcore_handler calls main(payload))."""
    config = get_config()
    if not config.dummy_portal_url:
        raise ValueError("DUMMY_PORTAL_URL is not configured")
    if not config.nova_act_search_workflow:
        raise ValueError("NOVA_ACT_SEARCH_WORKFLOW is not configured")

    inp = FlightSearchInput.model_validate(payload)
    base_url = config.dummy_portal_url
    search_url = build_search_url(inp.booking_plan, base_url)
    max_retries = int(os.environ.get("NOVA_ACT_MAX_RETRIES", "2"))

    start = time.monotonic()
    output: FlightSearchOutput | None = None
    recovery_strategies: list[str] = []
    dynamo = boto3.client("dynamodb")

    for attempt in range(max_retries + 1):
        try:
            with Workflow(**workflow_kwargs(config.nova_act_search_workflow)) as wf:
                kwargs = nova_act_kwargs(search_url, headless=config.nova_act_headless)
                kwargs["workflow"] = wf
                with NovaAct(**kwargs) as nova:
                    output = _run(nova, inp, base_url)
                    break  # success
        except (ActStateGuardrailError, ActGuardrailsError):
            log.error("nova_act_guardrail_violation", booking_id=inp.booking_id)
            raise
        except (ActExceededMaxStepsError, ActTimeoutError, ActRateLimitExceededError) as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            classified = classify_nova_act_error(exc, attempt, max_retries)
            recovery_strategies.append(classified.strategy.value)

            if config.audit_log_table:
                write_audit_log(dynamo, config.audit_log_table, build_recovery_audit_entry(
                    booking_id=inp.booking_id,
                    employee_id=inp.employee_id,
                    attempt=attempt,
                    strategy=classified.strategy.value,
                    error_type=classified.error_type,
                    success=False,
                    latency_ms=elapsed_ms,
                ))

            if classified.strategy == RecoveryStrategy.RETRY_WITH_WAIT and should_retry(elapsed_ms, classified.wait_seconds):
                log.info("retry_with_wait", attempt=attempt, wait_s=classified.wait_seconds, booking_id=inp.booking_id)
                time.sleep(classified.wait_seconds)
                continue

            output = _error_output(inp, base_url, classified.warning)
            break

    if output is None:
        output = _error_output(inp, base_url, "ACT_MAX_RETRIES_EXCEEDED")

    latency_ms = (time.monotonic() - start) * 1000
    log.info("flight_search_complete", booking_id=inp.booking_id, latency_ms=round(latency_ms), attempts=len(recovery_strategies) + 1)
    if config.audit_log_table:
        write_audit_log(dynamo, config.audit_log_table, build_flight_search_audit_entry(
            booking_id=inp.booking_id,
            employee_id=inp.employee_id,
            total_results=output.search_result.total_results,
            flights_returned=len(output.search_result.flights),
            fallback_url_set=output.fallback_url is not None,
            warnings=output.warnings,
            latency_ms=latency_ms,
            total_attempts=len(recovery_strategies) + 1,
            recovery_strategies_used=recovery_strategies,
        ))
    return output.model_dump()


if __name__ == "__main__":
    import json
    from datetime import date

    from core.models.booking import BookingPlan

    plan = BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))
    result = main(FlightSearchInput(booking_id="test-1", employee_id="emp-1", booking_plan=plan).model_dump())
    print(json.dumps(result, indent=2, default=str))
