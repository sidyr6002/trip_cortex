"""
Nova Act flight booking smoke test — visual browser demo.

Runs the full booking workflow with headless=False so you can watch
Nova Act control Chrome in real time. Connect via chrome://inspect
to see the DevTools view.

Usage:
    PYTHONPATH=src uv run pytest tests/smoke/test_nova_act_booking_smoke.py -v -s

Requirements:
    - .env configured with DUMMY_PORTAL_URL, PORTAL_TEST_EMAIL, PORTAL_TEST_PASSWORD
    - NOVA_ACT_BOOKING_WORKFLOW set (ACR workflow deployed)
    - NOVA_ACT_HEADLESS=false in .env (or overridden below)
    - AWS credentials configured (for Nova Act IAM auth)

chrome://inspect setup:
    The test launches Chrome with --remote-debugging-port=9222.
    Open chrome://inspect in your local Chrome, click "Configure...",
    add localhost:9222, and the Nova Act browser tab will appear
    under "Remote Target".
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("NOVA_ACT_BOOKING_WORKFLOW"),
        reason="NOVA_ACT_BOOKING_WORKFLOW not set — skip smoke test",
    ),
]


def _next_weekday(start: date, weekday: int = 0) -> date:
    """Return the next occurrence of `weekday` (0=Mon) on or after `start`."""
    days_ahead = weekday - start.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start + timedelta(days=days_ahead)


@pytest.fixture()
def booking_input():
    """Build a BookingInput for DEL → BOM on the next Monday."""
    from core.config import get_config
    from core.models.booking import BookingInput, BookingPlan, PassengerInfo
    from core.models.flight import FlightOption
    from core.services.flight_search import build_search_url

    config = get_config()
    assert config.dummy_portal_url, "DUMMY_PORTAL_URL must be set"

    departure = _next_weekday(date.today() + timedelta(days=1))
    plan = BookingPlan.strict_defaults("DEL", "BOM", departure)
    search_url = build_search_url(plan, config.dummy_portal_url)

    flight = FlightOption(
        airline="IndiGo",
        flight_number="6E-2134",
        price=98.0,
        departure_time="06:00",
        arrival_time="08:15",
        stops=0,
        cabin_class="Economy",
        duration="2h 15m",
    )
    passenger = PassengerInfo(
        first_name="Demo",
        last_name="Traveler",
        date_of_birth="15-06-1990",
        email="demo@tripcortex.dev",
        phone="+91 98765 43210",
    )

    return BookingInput(
        booking_id="smoke-demo-1",
        employee_id="emp-demo",
        flight=flight,
        booking_plan=plan,
        passengers=[passenger],
        search_url=search_url,
    )


def test_flight_booking_smoke(booking_input) -> None:
    """
    Run the full Nova Act booking flow with a visible browser.

    Watch the AI:
      1. Sign into FlySmart portal
      2. Find and select the IndiGo 6E-2134 flight
      3. Fill passenger details (Demo Traveler)
      4. Enter payment info (test card 4242...)
      5. Click Confirm & Pay
      6. Extract booking confirmation

    Open chrome://inspect → Configure → localhost:9222 to watch live.
    """
    # Force headless=false and remote debugging for this smoke test
    os.environ["NOVA_ACT_HEADLESS"] = "false"
    os.environ["NOVA_ACT_BROWSER_ARGS"] = "--remote-debugging-port=9222"

    # Reload config so it picks up the overridden env vars
    from core.config import _reset_config
    _reset_config()

    from booking_agent.flight_booking import main
    from core.models.booking import BookingOutput

    print("\n" + "=" * 60)
    print("  NOVA ACT SMOKE TEST — FLIGHT BOOKING")
    print("  Open chrome://inspect → Configure → localhost:9222")
    print("=" * 60)
    print(f"\n  Route:     DEL → BOM")
    print(f"  Flight:    {booking_input.flight.airline} {booking_input.flight.flight_number}")
    print(f"  Passenger: {booking_input.passengers[0].first_name} {booking_input.passengers[0].last_name}")
    print(f"  Search:    {booking_input.search_url}")
    print(f"\n  Starting Nova Act browser automation...\n")

    result = main(booking_input.model_dump())
    output = BookingOutput.model_validate(result)

    print("\n" + "-" * 60)
    if output.confirmation:
        print(f"  ✅ BOOKING CONFIRMED")
        print(f"  Reference:  {output.confirmation.booking_reference}")
        print(f"  Payment:    {output.confirmation.payment_reference}")
        print(f"  Amount:     ${output.confirmation.total_amount:.2f}")
        print(f"  Flight:     {output.confirmation.flight_number}")
    else:
        print(f"  ⚠️  FALLBACK — no confirmation captured")
        print(f"  Fallback URL: {output.fallback_url}")
        print(f"  Warnings:     {output.warnings}")
    print("-" * 60 + "\n")

    print(json.dumps(result, indent=2, default=str))

    assert output.confirmation is not None, f"Booking failed — warnings: {output.warnings}"
    assert output.confirmation.booking_reference.startswith("FS-")
    assert output.confirmation.total_amount > 0
