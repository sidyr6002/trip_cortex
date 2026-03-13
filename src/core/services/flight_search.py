"""Pure functions for building Nova Act search inputs and filtering results."""

from urllib.parse import urlencode, urlparse, urlunparse

from core.models.booking import BookingPlan, PolicyConstraints
from core.models.flight import FlightSearchResult


def build_search_url(plan: BookingPlan, base_url: str) -> str:
    p = plan.parameters
    query = urlencode({
        "from": p.origin,
        "to": p.destination,
        "date": p.departure_date.isoformat(),
        "class": p.cabin_class,
    })
    parsed = urlparse(base_url)
    return urlunparse(parsed._replace(path="/search", query=query))


def build_filter_prompt(constraints: PolicyConstraints) -> str | None:
    if constraints.preferred_vendors == ["any"]:
        return None
    vendors = ", ".join(constraints.preferred_vendors)
    return f"Filter results to show only flights from: {vendors}"


def build_fallback_url(plan: BookingPlan, base_url: str) -> str:
    return build_search_url(plan, base_url)


def filter_by_constraints(
    result: FlightSearchResult,
    constraints: PolicyConstraints,
) -> tuple[FlightSearchResult, list[str]]:
    flights = result.flights

    flights = [f for f in flights if f.price <= constraints.max_budget_usd]

    if constraints.preferred_vendors != ["any"]:
        vendors_lower = [v.lower() for v in constraints.preferred_vendors]
        flights = [
            f for f in flights
            if any(v in f.airline.lower() for v in vendors_lower)
        ]

    warnings: list[str] = []
    if not flights:
        warnings.append("NO_FLIGHTS_AFTER_FILTER")

    filtered = result.model_copy(update={"flights": flights, "total_results": len(flights)})
    return filtered, warnings
