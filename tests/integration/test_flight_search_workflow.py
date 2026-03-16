"""
Integration test: flight_search.py main() against FlySmart dummy portal.

Requirements:
    - AWS credentials configured
    - NOVA_ACT_SEARCH_WORKFLOW and DUMMY_PORTAL_URL set in environment
"""

import os
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytestmark = pytest.mark.skipif(
    not os.environ.get("NOVA_ACT_SEARCH_WORKFLOW"),
    reason="NOVA_ACT_SEARCH_WORKFLOW not set",
)


@pytest.mark.integration
def test_flight_search_workflow() -> None:
    from booking_agent.flight_search import main
    from core.models.booking import BookingPlan
    from core.models.flight import FlightSearchInput, FlightSearchOutput

    plan = BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))
    # Override strict defaults: budget $200, any vendor
    plan = plan.model_copy(update={
        "policy_constraints": plan.policy_constraints.model_copy(
            update={"max_budget_usd": 200.0, "preferred_vendors": ["any"]}
        )
    })

    payload = FlightSearchInput(booking_id="integ-1", employee_id="emp-1", booking_plan=plan).model_dump()
    result = main(payload)
    output = FlightSearchOutput.model_validate(result)

    assert len(output.search_result.flights) >= 1
    assert all(f.price <= 200.0 for f in output.search_result.flights)
    assert output.fallback_url is None, f"Unexpected fallback_url: {output.fallback_url}"
    assert output.warnings == [], f"Unexpected warnings: {output.warnings}"
