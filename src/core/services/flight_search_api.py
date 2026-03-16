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
