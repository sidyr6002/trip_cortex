"""
Integration test: flight_booking.py main() against FlySmart dummy portal.

Requirements:
    - AWS credentials configured
    - NOVA_ACT_BOOKING_WORKFLOW, NOVA_ACT_SEARCH_WORKFLOW, and DUMMY_PORTAL_URL set in environment
"""

import os
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytestmark = pytest.mark.skipif(
    not os.environ.get("NOVA_ACT_BOOKING_WORKFLOW"),
    reason="NOVA_ACT_BOOKING_WORKFLOW not set",
)


@pytest.mark.integration
def test_flight_booking_workflow() -> None:
    from booking_agent.flight_booking import main

    from core.config import get_config
    from core.models.booking import BookingInput, BookingOutput, BookingPlan, PassengerInfo
    from core.models.flight import FlightOption
    from core.services.flight_search import build_search_url

    plan = BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))
    config = get_config()
    search_url = build_search_url(plan, config.dummy_portal_url or "")

    flight = FlightOption(
        airline="SpiceJet", flight_number="SG-8194", price=150.0,
        departure_time="06:00", arrival_time="08:10", stops=0, cabin_class="economy",
    )
    passenger = PassengerInfo(
        first_name="Test", last_name="Traveler", date_of_birth="15-06-1990",
        email="test@example.com", phone="+1 555 000 0000",
    )
    inp = BookingInput(
        booking_id="integ-booking-1",
        employee_id="emp-1",
        flight=flight,
        booking_plan=plan,
        passengers=[passenger],
        search_url=search_url,
    )

    result = main(inp.model_dump())
    output = BookingOutput.model_validate(result)

    assert output.confirmation is not None, f"No confirmation — warnings: {output.warnings}"
    assert output.confirmation.booking_reference.startswith("FS-")
    assert output.confirmation.total_amount > 0
    assert output.fallback_url is None, f"Unexpected fallback_url: {output.fallback_url}"
    assert output.warnings == [], f"Unexpected warnings: {output.warnings}"
