"""
Flight search Nova Act workflow script for FlySmart dummy portal.

Local dev:
    .venv/bin/python src/nova_act/flight_search.py

ACR deployment entry point: flight_search() (decorated with @workflow)
"""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import boto3  # noqa: E402
import structlog  # noqa: E402

from nova_act import (  # noqa: E402
    ActExceededMaxStepsError,
    ActGuardrailsError,
    ActStateGuardrailError,
    ActTimeoutError,
    NovaAct,
    Workflow,
    workflow,
)

_script_dir = Path(__file__).parent
sys.path.insert(0, str(next(p for p in [_script_dir, _script_dir.parent] if (p / "core").is_dir())))
from core.config import get_config  # noqa: E402
from core.models.flight import FlightSearchInput, FlightSearchOutput, FlightSearchResult  # noqa: E402
from core.services.audit import build_flight_search_audit_entry, write_audit_log  # noqa: E402
from core.services.flight_search import (  # noqa: E402
    build_fallback_url,
    build_filter_prompt,
    build_search_url,
    filter_by_constraints,
)

sys.path.insert(0, str(Path(__file__).parent))
from config import nova_act_kwargs, workflow_kwargs  # noqa: E402

log = structlog.get_logger()

_EXTRACT_PROMPT = (
    "Extract all available (not sold out) flight options from the search results. "
    "For each flight include: airline name, flight number, price in USD (numeric only), "
    "departure time, arrival time, number of stops (0 for Direct), cabin class, and duration."
)


def _run(nova: NovaAct, inp: FlightSearchInput, base_url: str) -> FlightSearchOutput:
    constraints = inp.booking_plan.policy_constraints
    warnings: list[str] = []

    # Step 1 (optional): browser-side vendor filter before extraction
    filter_prompt = build_filter_prompt(constraints)
    if filter_prompt:
        nova.act(filter_prompt)

    # Step 2: structured extraction
    result = nova.act_get(_EXTRACT_PROMPT, schema=FlightSearchResult.model_json_schema(), max_steps=50)
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

    # Step 3: Python safety-net filter
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
        fallback_url=build_fallback_url(inp.booking_plan, base_url),
        warnings=[warning],
    )


def main(payload: dict) -> dict:
    """Local dev entry point — manages Workflow/NovaAct lifecycle explicitly."""
    config = get_config()
    if not config.dummy_portal_url:
        raise ValueError("DUMMY_PORTAL_URL is not configured")
    inp = FlightSearchInput.model_validate(payload)
    base_url = config.dummy_portal_url
    search_url = build_search_url(inp.booking_plan, base_url)

    if not config.nova_act_search_workflow:
        raise ValueError("NOVA_ACT_SEARCH_WORKFLOW is not configured")
    start = time.monotonic()
    output: FlightSearchOutput | None = None
    try:
        with Workflow(**workflow_kwargs(config.nova_act_search_workflow)) as wf:
            kwargs = nova_act_kwargs(search_url, headless=config.nova_act_headless)
            kwargs["workflow"] = wf
            with NovaAct(**kwargs) as nova:
                output = _run(nova, inp, base_url)
    except (ActStateGuardrailError, ActGuardrailsError):
        log.error("nova_act_guardrail_violation", booking_id=inp.booking_id)
        raise
    except ActExceededMaxStepsError:
        log.warning("nova_act_max_steps_exceeded", booking_id=inp.booking_id)
        output = _error_output(inp, base_url, "ACT_EXCEEDED_MAX_STEPS")
    except ActTimeoutError:
        log.warning("nova_act_timeout", booking_id=inp.booking_id)
        output = _error_output(inp, base_url, "ACT_TIMEOUT")
    finally:
        latency_ms = (time.monotonic() - start) * 1000
        log.info("flight_search_complete", booking_id=inp.booking_id, latency_ms=round(latency_ms))
        if output is not None and config.audit_log_table:
            entry = build_flight_search_audit_entry(
                booking_id=inp.booking_id,
                employee_id=inp.employee_id,
                total_results=output.search_result.total_results,
                flights_returned=len(output.search_result.flights),
                fallback_url_set=output.fallback_url is not None,
                warnings=output.warnings,
                latency_ms=latency_ms,
            )
            write_audit_log(boto3.client("dynamodb"), config.audit_log_table, entry)
    return output.model_dump()  # type: ignore[union-attr]


@workflow(model_id="nova-act-latest", workflow_definition_name="trip-cortex-flight-search")
def flight_search(nova: NovaAct, payload: dict) -> dict:
    """ACR deployment entry point — @workflow manages Workflow lifecycle."""
    config = get_config()
    if not config.dummy_portal_url:
        raise ValueError("DUMMY_PORTAL_URL is not configured")
    inp = FlightSearchInput.model_validate(payload)
    base_url = config.dummy_portal_url
    return _run(nova, inp, base_url).model_dump()


if __name__ == "__main__":
    import json
    from datetime import date

    from core.models.booking import BookingPlan

    plan = BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))
    result = main(FlightSearchInput(booking_id="test-1", employee_id="emp-1", booking_plan=plan).model_dump())
    print(json.dumps(result, indent=2, default=str))
