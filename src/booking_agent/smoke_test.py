"""
Smoke test for Nova Act flight search against the FlySmart dummy portal.

Usage:
    PYTHONPATH=src uv run python src/booking_agent/smoke_test.py

Requirements:
    - AWS credentials configured (aws sts get-caller-identity)
    - NOVA_ACT_SEARCH_WORKFLOW set in .env
    - DUMMY_PORTAL_URL set in .env (defaults to https://flysmart.dportal.workers.dev)
"""

from pathlib import Path

# Load .env before any other imports
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from nova_act import NovaAct, Workflow  # noqa: E402

try:
    from booking_agent.config import nova_act_kwargs, workflow_kwargs  # PYTHONPATH=src (local/test)
except ModuleNotFoundError:
    from config import nova_act_kwargs, workflow_kwargs  # type: ignore[no-redef]  # ACR flat layout
from core.config import get_config  # noqa: E402
from core.models.flight import FlightSearchResult  # noqa: E402


def main() -> None:
    config = get_config()

    portal_url = config.dummy_portal_url or "https://flysmart.dportal.workers.dev"
    search_url = f"{portal_url}/search?from=DEL&to=BOM&date=2026-03-16&class=economy"

    print(f"Starting smoke test against: {portal_url}")
    print(f"Workflow: {config.nova_act_search_workflow}")

    with Workflow(**workflow_kwargs(config.nova_act_search_workflow)) as workflow:
        kwargs = nova_act_kwargs(search_url, headless=config.nova_act_headless)
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

    print(f"\nFound {flights.total_results} flights ({len(flights.flights)} extracted):")
    for f in flights.flights:
        print(
            f"  {f.airline} {f.flight_number} | {f.departure_time} → {f.arrival_time} "
            f"| ${f.price} | {f.stops} stops | {f.duration}"
        )

    assert len(flights.flights) > 0, "No flights extracted"
    assert all(f.price > 0 for f in flights.flights), "Invalid price found"
    print("\n✅ Smoke test passed")


if __name__ == "__main__":
    main()
