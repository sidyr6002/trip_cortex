"""
Flight booking Nova Act workflow script for FlySmart dummy portal.

Local dev:
    PYTHONPATH=src .venv/bin/python src/booking_agent/flight_booking.py

ACR entry point: main(payload) — called by agentcore_handler.py
"""

import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import boto3
import structlog
from nova_act import (
    ActExceededMaxStepsError,
    ActGuardrailsError,
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
from core.services.audit import write_audit_log
from core.services.flight_booking import (
    build_booking_audit_entry,
    build_passenger_prompt,
    build_select_flight_prompt,
)



log = structlog.get_logger()


def _sign_in(nova: NovaAct, email: str, password: str, search_url: str) -> None:
    """Sign in via email+password on the FlySmart login page, then navigate to search."""
    nova.act(f"Type '{email}' into the email field and '{password}' into the password field, then click 'Sign In'")
    nova.act(f"Navigate to {search_url}")


def _run(nova: NovaAct, inp: BookingInput, email: str, password: str) -> BookingOutput:
    # Step 0: sign in and navigate to search results
    _sign_in(nova, email, password, inp.search_url)

    # Step 1: select flight from search results
    nova.act(build_select_flight_prompt(inp.flight))

    # Step 1: review page
    nova.act("Click the 'Continue to Passenger Details' button")

    # Step 2: fill passenger form
    for i, passenger in enumerate(inp.passengers):
        nova.act(build_passenger_prompt(passenger, i, is_primary=(i == 0)))
    nova.act("Click 'Continue to Payment'")

    # Step 3: Stripe payment
    nova.act("Enter card number 4242 4242 4242 4242 in the payment form")
    nova.act("Enter expiry date 12/30 and CVC 123")
    nova.act("Check the terms and conditions checkbox")
    nova.act("Click the 'Confirm & Pay' button")

    # Step 4: extract confirmation
    result = nova.act_get(
        "Extract the booking reference, payment reference, total amount, and flight number from this confirmation page",
        schema=BookingConfirmation.model_json_schema(),
        max_steps=50,
    )
    confirmation = BookingConfirmation.model_validate(result.parsed_response)

    return BookingOutput(
        booking_id=inp.booking_id,
        employee_id=inp.employee_id,
        confirmation=confirmation,
    )


def _error_output(inp: BookingInput, warning: str) -> BookingOutput:
    return BookingOutput(
        booking_id=inp.booking_id,
        employee_id=inp.employee_id,
        fallback_url=inp.search_url,
        warnings=[warning],
    )


def main(payload: dict) -> dict:
    """Entry point for both local dev and ACR (agentcore_handler calls main(payload))."""
    config = get_config()
    if not config.dummy_portal_url:
        raise ValueError("DUMMY_PORTAL_URL is not configured")
    inp = BookingInput.model_validate(payload)

    if not config.nova_act_booking_workflow:
        raise ValueError("NOVA_ACT_BOOKING_WORKFLOW is not configured")
    if not config.portal_test_email or not config.portal_test_password:
        raise ValueError("PORTAL_TEST_EMAIL and PORTAL_TEST_PASSWORD must be configured")
    login_url = f"{config.dummy_portal_url}/login"
    start = time.monotonic()
    output: BookingOutput | None = None
    try:
        with Workflow(**workflow_kwargs(config.nova_act_booking_workflow)) as wf:
            kwargs = nova_act_kwargs(login_url, headless=config.nova_act_headless)
            kwargs["workflow"] = wf
            with NovaAct(**kwargs) as nova:
                output = _run(nova, inp, config.portal_test_email, config.portal_test_password)
    except (ActStateGuardrailError, ActGuardrailsError):
        log.error("nova_act_guardrail_violation", booking_id=inp.booking_id)
        raise
    except ActExceededMaxStepsError:
        log.warning("nova_act_max_steps_exceeded", booking_id=inp.booking_id)
        output = _error_output(inp, "ACT_EXCEEDED_MAX_STEPS")
    except ActTimeoutError:
        log.warning("nova_act_timeout", booking_id=inp.booking_id)
        output = _error_output(inp, "ACT_TIMEOUT")
    finally:
        latency_ms = (time.monotonic() - start) * 1000
        log.info("flight_booking_complete", booking_id=inp.booking_id, latency_ms=round(latency_ms))
        if output is not None and config.audit_log_table:
            entry = build_booking_audit_entry(
                booking_id=inp.booking_id,
                employee_id=inp.employee_id,
                confirmation=output.confirmation,
                fallback_url_set=output.fallback_url is not None,
                warnings=output.warnings,
                latency_ms=latency_ms,
            )
            write_audit_log(boto3.client("dynamodb"), config.audit_log_table, entry)
    return output.model_dump()  # type: ignore[union-attr]


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
        airline="SpiceJet",
        flight_number="SG-8194",
        price=150.0,
        departure_time="06:00",
        arrival_time="08:10",
        stops=0,
        cabin_class="economy",
        duration="2h 10m",
    )
    passenger = PassengerInfo(
        first_name="Test",
        last_name="Traveler",
        date_of_birth="15-06-1990",
        email="test@example.com",
        phone="+1 555 000 0000",
    )
    inp = BookingInput(
        booking_id="test-1",
        employee_id="emp-1",
        flight=flight,
        booking_plan=plan,
        passengers=[passenger],
        search_url=search_url,
    )
    result = main(inp.model_dump())
    print(json.dumps(result, indent=2, default=str))
