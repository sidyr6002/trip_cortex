"""
Integration test: Nova Act flight search against FlySmart dummy portal.

Requirements:
    - AWS credentials configured
    - NOVA_ACT_SEARCH_WORKFLOW set in environment
    - Dummy portal reachable at DUMMY_PORTAL_URL
"""

import os
import sys
from pathlib import Path

import pytest

# Import the SDK before src/ is on sys.path to avoid nova_act package shadowing.
# pytest adds src/ via pythonpath config, which shadows the installed nova_act SDK.
_sdk_path = str(Path(__file__).parent.parent.parent / ".venv" / "lib")
_sdk_dirs = list(Path(_sdk_path).glob("python*/site-packages"))
if _sdk_dirs:
    sys.path.insert(0, str(_sdk_dirs[0]))

from nova_act import NovaAct, Workflow  # noqa: E402 — must come after path fix

# Now safe to add src/ for core imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "nova_act"))

pytestmark = pytest.mark.skipif(
    not os.environ.get("NOVA_ACT_SEARCH_WORKFLOW"),
    reason="NOVA_ACT_SEARCH_WORKFLOW not set — requires AWS IAM auth and workflow definitions",
)


@pytest.mark.integration
def test_nova_act_flight_search() -> None:
    """Full loop: Nova Act searches FlySmart, extracts flights, validates against Pydantic schema."""
    from config import nova_act_kwargs, workflow_kwargs  # nova_act/config.py

    from core.config import get_config
    from core.models.flight import FlightSearchResult

    config = get_config()
    portal_url = config.dummy_portal_url or "https://flysmart.dportal.workers.dev"
    search_url = f"{portal_url}/search?from=DEL&to=BOM&date=2026-03-16&class=economy"

    with Workflow(**workflow_kwargs(config.nova_act_search_workflow)) as workflow:
        kwargs = nova_act_kwargs(search_url, headless=True)
        kwargs["workflow"] = workflow

        with NovaAct(**kwargs) as nova:
            result = nova.act_get(
                "Extract all available (not sold out) flight options from the search results. "
                "For each flight include: airline name, flight number, price in USD (numeric only), "
                "departure time, arrival time, number of stops (0 for Direct), cabin class, and duration.",
                schema=FlightSearchResult.model_json_schema(),
                max_steps=50,
            )

    flights = FlightSearchResult.model_validate(result.parsed_response)

    assert len(flights.flights) >= 1, "Expected at least 1 flight option"
    assert all(f.price > 0 for f in flights.flights), "All prices must be positive"
    assert flights.search_origin == "DEL"
    assert flights.search_destination == "BOM"
