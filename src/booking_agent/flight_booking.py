"""
Flight booking Nova Act workflow script for FlySmart dummy portal.

Local dev:
    PYTHONPATH=src .venv/bin/python src/booking_agent/flight_booking.py

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
from core.models.booking import BookingConfirmation, BookingInput, BookingOutput
from core.services.audit import build_recovery_audit_entry, write_audit_log
from core.services.error_classification import RecoveryStrategy, classify_nova_act_error
from core.services.flight_booking import (
    build_booking_audit_entry,
    build_booking_fallback_url,
    build_passenger_prompt,
    build_select_flight_prompt,
)
from core.services.nova_act_recovery import reorient, should_retry

log = structlog.get_logger()


def _sign_in(nova: NovaAct, email: str, password: str, search_url: str) -> None:
    """Sign in via email+password on the FlySmart login page, then navigate to search."""
    nova.act(f"Type '{email}' into the email field and '{password}' into the password field, then click 'Sign In'")
    nova.act(f"Navigate to {search_url}")


def _run(nova: NovaAct, inp: BookingInput, email: str, password: str, *, allow_reorient: bool = True) -> BookingOutput:
    _sign_in(nova, email, password, inp.search_url)

    try:
        nova.act(build_select_flight_prompt(inp.flight))
        nova.act("Click the 'Continue to Passenger Details' button")
        for i, passenger in enumerate(inp.passengers):
            nova.act(build_passenger_prompt(passenger, i, is_primary=(i == 0)))
        nova.act("Click 'Continue to Payment'")
        nova.act("Enter card number 4242 4242 4242 4242 in the payment form")
        nova.act("Enter expiry date 12/30 and CVC 123")
        nova.act("Check the terms and conditions checkbox")
        nova.act("Click the 'Confirm & Pay' button")
    except ActExceededMaxStepsError:
        if allow_reorient and reorient(nova, build_select_flight_prompt(inp.flight), inp.search_url):
            return _run(nova, inp, email, password, allow_reorient=False)
        raise

    result = nova.act_get(
        "Extract the booking reference, payment reference, total amount, and flight number from this confirmation page",
        schema=BookingConfirmation.model_json_schema(),
        max_steps=50,
    )
    confirmation = BookingConfirmation.model_validate(result.parsed_response)
    return BookingOutput(booking_id=inp.booking_id, employee_id=inp.employee_id, confirmation=confirmation)


def _error_output(inp: BookingInput, warning: str) -> BookingOutput:
    return BookingOutput(
        booking_id=inp.booking_id,
        employee_id=inp.employee_id,
        fallback_url=build_booking_fallback_url(inp.flight, inp.search_url, warning),
        warnings=[warning],
    )


def main(payload: dict) -> dict:
    """Entry point for both local dev and ACR (agentcore_handler calls main(payload))."""
    config = get_config()
    if not config.dummy_portal_url:
        raise ValueError("DUMMY_PORTAL_URL is not configured")
    if not config.nova_act_booking_workflow:
        raise ValueError("NOVA_ACT_BOOKING_WORKFLOW is not configured")
    if not config.portal_test_email or not config.portal_test_password:
        raise ValueError("PORTAL_TEST_EMAIL and PORTAL_TEST_PASSWORD must be configured")

    inp = BookingInput.model_validate(payload)
    login_url = f"{config.dummy_portal_url}/login"
    max_retries = int(os.environ.get("NOVA_ACT_MAX_RETRIES", "2"))

    start = time.monotonic()
    output: BookingOutput | None = None
    recovery_strategies: list[str] = []
    dynamo = boto3.client("dynamodb")

    for attempt in range(max_retries + 1):
        try:
            with Workflow(**workflow_kwargs(config.nova_act_booking_workflow)) as wf:
                kwargs = nova_act_kwargs(login_url, headless=config.nova_act_headless)
                kwargs["workflow"] = wf
                with NovaAct(**kwargs) as nova:
                    output = _run(nova, inp, config.portal_test_email, config.portal_test_password)
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

            output = _error_output(inp, classified.warning)
            break

    if output is None:
        output = _error_output(inp, "ACT_MAX_RETRIES_EXCEEDED")

    latency_ms = (time.monotonic() - start) * 1000
    log.info("flight_booking_complete", booking_id=inp.booking_id, latency_ms=round(latency_ms), attempts=len(recovery_strategies) + 1)
    if config.audit_log_table:
        write_audit_log(dynamo, config.audit_log_table, build_booking_audit_entry(
            booking_id=inp.booking_id,
            employee_id=inp.employee_id,
            confirmation=output.confirmation,
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

    from core.models.booking import BookingPlan, PassengerInfo
    from core.models.flight import FlightOption
    from core.services.flight_search import build_search_url

    plan = BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))
    config = get_config()
    search_url = build_search_url(plan, config.dummy_portal_url or "")
    flight = FlightOption(
        airline="SpiceJet", flight_number="SG-8194", price=150.0,
        departure_time="06:00", arrival_time="08:10", stops=0,
        cabin_class="economy", duration="2h 10m",
    )
    passenger = PassengerInfo(
        first_name="Test", last_name="Traveler", date_of_birth="15-06-1990",
        email="test@example.com", phone="+1 555 000 0000",
    )
    inp = BookingInput(
        booking_id="test-1", employee_id="emp-1", flight=flight,
        booking_plan=plan, passengers=[passenger], search_url=search_url,
    )
    result = main(inp.model_dump())
    print(json.dumps(result, indent=2, default=str))
