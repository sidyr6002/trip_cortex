"""Flight search via dummy portal REST API — replaces ACR/Nova Act for search step."""

import urllib.request
import urllib.parse
import json
from typing import Any

from core.config import Config
from core.models.flight import FlightOption, FlightSearchOutput, FlightSearchResult


def search_flights_via_api(event: dict[str, Any], config: Config) -> dict[str, Any]:
    plan = event["plan"]
    params = plan["parameters"]

    query = urllib.parse.urlencode({
        "from": params["origin"],
        "to": params["destination"],
        "date": params["departure_date"],
        "class": params["cabin_class"],
    })
    req = urllib.request.Request(
        f"{config.dummy_portal_url}/api/flights?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    flights = [_to_flight_option(f) for f in data["flights"]]

    constraints = plan.get("policy_constraints", {})
    flights = _apply_policy_filters(flights, constraints)

    result = FlightSearchOutput(
        booking_id=event["booking_id"],
        employee_id=event["employee_id"],
        search_result=FlightSearchResult(
            flights=flights,
            search_origin=params["origin"],
            search_destination=params["destination"],
            search_date=params["departure_date"],
            total_results=len(flights),
        ),
    )
    return result.model_dump()


def _to_flight_option(f: dict[str, Any]) -> FlightOption:
    seg = f["segments"][0]
    dep = seg["departureTime"][11:16]  # HH:MM
    arr = f["segments"][-1]["arrivalTime"][11:16]
    stops = len(f["segments"]) - 1
    mins = f["totalDurationMinutes"]

    return FlightOption(
        airline=seg["airline"]["name"],
        flight_number=seg["flightNumber"],
        price=float(f["pricing"]["pricePerPassenger"]),
        departure_time=dep,
        arrival_time=arr,
        stops=stops,
        cabin_class=f["flightClass"]["name"],
        duration=f"{mins // 60}h {mins % 60}m",
    )


def _apply_policy_filters(
    flights: list[FlightOption], constraints: dict[str, Any]
) -> list[FlightOption]:
    max_budget = constraints.get("max_budget_usd")
    vendors = [v.lower() for v in constraints.get("preferred_vendors", []) if v.lower() != "any"]

    compliant: list[FlightOption] = []
    non_compliant: list[FlightOption] = []

    for f in flights:
        notes: list[str] = []
        if max_budget and f.price > max_budget:
            notes.append(f"Over budget (${f.price:.0f} > ${max_budget:.0f})")
        if vendors and f.airline.lower() not in vendors:
            notes.append(f"Non-preferred airline ({f.airline})")

        tagged = f.model_copy(update={"compliant": len(notes) == 0, "policy_notes": notes})
        (compliant if tagged.compliant else non_compliant).append(tagged)

    # Return compliant first, then non-compliant — show all so user has context
    return compliant + non_compliant
