"""Unit tests for src/core/services/flight_booking.py — pure functions, no Nova Act, no AWS."""

import pytest

from core.models.booking import BookingConfirmation, PassengerInfo
from core.models.flight import FlightOption
from core.services.flight_booking import (
    build_booking_audit_entry,
    build_passenger_prompt,
    build_select_flight_prompt,
)


@pytest.fixture
def flight() -> FlightOption:
    return FlightOption(
        airline="SpiceJet", flight_number="SG-8194", price=150.0,
        departure_time="06:00", arrival_time="08:10", stops=0, cabin_class="economy",
    )


@pytest.fixture
def primary() -> PassengerInfo:
    return PassengerInfo(
        first_name="John", last_name="Doe", date_of_birth="15-06-1990",
        email="john@example.com", phone="+1 555 000 0000",
    )


@pytest.fixture
def secondary() -> PassengerInfo:
    return PassengerInfo(first_name="Jane", last_name="Doe", date_of_birth="20-08-1992")


@pytest.fixture
def confirmation() -> BookingConfirmation:
    return BookingConfirmation(
        booking_reference="FS-SG8194-ABC123",
        payment_reference="pi_test_123",
        total_amount=150.0,
        flight_number="SG-8194",
    )


class TestBuildSelectFlightPrompt:
    def test_includes_airline_and_flight_number(self, flight: FlightOption) -> None:
        prompt = build_select_flight_prompt(flight)
        assert "SpiceJet" in prompt
        assert "SG-8194" in prompt

    def test_mentions_select_flight(self, flight: FlightOption) -> None:
        assert "Select Flight" in build_select_flight_prompt(flight)


class TestBuildPassengerPrompt:
    def test_primary_includes_email_and_phone(self, primary: PassengerInfo) -> None:
        prompt = build_passenger_prompt(primary, 0, is_primary=True)
        assert "john@example.com" in prompt
        assert "+1 555 000 0000" in prompt

    def test_primary_includes_name_and_dob(self, primary: PassengerInfo) -> None:
        prompt = build_passenger_prompt(primary, 0, is_primary=True)
        assert "John" in prompt
        assert "Doe" in prompt
        assert "15-06-1990" in prompt

    def test_secondary_excludes_email_and_phone(self, secondary: PassengerInfo) -> None:
        prompt = build_passenger_prompt(secondary, 1, is_primary=False)
        assert "email" not in prompt.lower()
        assert "phone" not in prompt.lower()

    def test_secondary_includes_name_and_dob(self, secondary: PassengerInfo) -> None:
        prompt = build_passenger_prompt(secondary, 1, is_primary=False)
        assert "Jane" in prompt
        assert "20-08-1992" in prompt


class TestBuildBookingAuditEntry:
    def test_success_includes_booking_reference(self, confirmation: BookingConfirmation) -> None:
        entry = build_booking_audit_entry("b-1", "e-1", confirmation, False, [], 100.0)
        assert entry["output"]["booking_reference"] == "FS-SG8194-ABC123"
        assert entry["output"]["total_amount"] == 150.0

    def test_failure_has_none_fields(self) -> None:
        entry = build_booking_audit_entry("b-1", "e-1", None, True, ["ACT_TIMEOUT"], 200.0)
        assert entry["output"]["booking_reference"] is None
        assert entry["output"]["total_amount"] is None
        assert entry["output"]["fallback_url_set"] is True

    def test_no_pii_in_audit_entry(self, confirmation: BookingConfirmation) -> None:
        passenger = PassengerInfo(
            first_name="John", last_name="Doe", date_of_birth="15-06-1990",
            email="john@example.com", phone="+1 555 000 0000",
        )
        entry = build_booking_audit_entry("b-1", "e-1", confirmation, False, [], 100.0)
        serialized = str(entry)
        assert passenger.first_name not in serialized
        assert passenger.last_name not in serialized
        assert (passenger.email or "") not in serialized
        assert (passenger.phone or "") not in serialized
        assert passenger.date_of_birth not in serialized
