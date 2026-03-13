"""Unit tests for src/core/services/flight_search.py — pure functions, no Nova Act, no AWS."""

from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest

from core.models.booking import BookingPlan
from core.models.flight import FlightOption, FlightSearchResult
from core.services.flight_search import (
    build_fallback_url,
    build_filter_prompt,
    build_search_url,
    filter_by_constraints,
)

BASE_URL = "https://flysmart.dportal.workers.dev"


@pytest.fixture
def plan() -> BookingPlan:
    return BookingPlan.strict_defaults("DEL", "BOM", date(2026, 3, 16))


@pytest.fixture
def flights() -> list[FlightOption]:
    def _f(airline: str, number: str, price: float) -> FlightOption:
        return FlightOption(
            airline=airline, flight_number=number, price=price,
            departure_time="08:00", arrival_time="10:00", stops=0, cabin_class="economy",
        )
    return [_f("IndiGo", "6E-100", 80.0), _f("SpiceJet", "SG-200", 250.0), _f("Air India", "AI-300", 400.0)]


@pytest.fixture
def result(flights: list[FlightOption]) -> FlightSearchResult:
    return FlightSearchResult(
        flights=flights, search_origin="DEL", search_destination="BOM",
        search_date="2026-03-16", total_results=3,
    )


def _parse_url(url: str) -> tuple[str, dict]:
    parsed = urlparse(url)
    return parsed.path, {k: v[0] for k, v in parse_qs(parsed.query).items()}


class TestBuildSearchUrl:
    def test_correct_params(self, plan: BookingPlan) -> None:
        url = build_search_url(plan, BASE_URL)
        path, params = _parse_url(url)
        assert path == "/search"
        assert params == {"from": "DEL", "to": "BOM", "date": "2026-03-16", "class": "economy"}

    def test_preserves_base_url(self, plan: BookingPlan) -> None:
        url = build_search_url(plan, BASE_URL)
        assert url.startswith(BASE_URL)

    @pytest.mark.parametrize("cabin", ["economy", "business", "premium_economy", "first"])
    def test_all_cabin_classes(self, plan: BookingPlan, cabin: str) -> None:
        p = plan.model_copy(update={"parameters": plan.parameters.model_copy(update={"cabin_class": cabin})})
        _, params = _parse_url(build_search_url(p, BASE_URL))
        assert params["class"] == cabin


class TestBuildFilterPrompt:
    def test_any_returns_none(self, plan: BookingPlan) -> None:
        assert build_filter_prompt(plan.policy_constraints) is None

    def test_vendors_included_in_prompt(self, plan: BookingPlan) -> None:
        c = plan.policy_constraints.model_copy(update={"preferred_vendors": ["IndiGo", "Air India"]})
        prompt = build_filter_prompt(c)
        assert prompt is not None
        assert "IndiGo" in prompt
        assert "Air India" in prompt


class TestBuildFallbackUrl:
    def test_delegates_to_search_url(self, plan: BookingPlan) -> None:
        assert build_fallback_url(plan, BASE_URL) == build_search_url(plan, BASE_URL)

    def test_contains_all_params(self, plan: BookingPlan) -> None:
        _, params = _parse_url(build_fallback_url(plan, BASE_URL))
        assert {"from", "to", "date", "class"} <= params.keys()


class TestFilterByConstraints:
    def test_budget_removes_expensive_flights(self, result: FlightSearchResult, plan: BookingPlan) -> None:
        c = plan.policy_constraints.model_copy(update={"max_budget_usd": 200.0, "preferred_vendors": ["any"]})
        filtered, warnings = filter_by_constraints(result, c)
        assert all(f.price <= 200.0 for f in filtered.flights)
        assert filtered.total_results == len(filtered.flights)
        assert warnings == []

    def test_vendor_filter(self, result: FlightSearchResult, plan: BookingPlan) -> None:
        c = plan.policy_constraints.model_copy(update={"max_budget_usd": 500.0, "preferred_vendors": ["indigo"]})
        filtered, warnings = filter_by_constraints(result, c)
        assert all("indigo" in f.airline.lower() for f in filtered.flights)
        assert warnings == []

    def test_any_vendor_no_filtering(self, result: FlightSearchResult, plan: BookingPlan) -> None:
        c = plan.policy_constraints.model_copy(update={"max_budget_usd": 500.0, "preferred_vendors": ["any"]})
        filtered, warnings = filter_by_constraints(result, c)
        assert len(filtered.flights) == 3
        assert warnings == []

    def test_all_filtered_out_warning(self, result: FlightSearchResult, plan: BookingPlan) -> None:
        c = plan.policy_constraints.model_copy(update={"max_budget_usd": 10.0, "preferred_vendors": ["any"]})
        filtered, warnings = filter_by_constraints(result, c)
        assert filtered.flights == []
        assert "NO_FLIGHTS_AFTER_FILTER" in warnings
