from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.models.booking import BookingConfirmation, PassengerInfo
from core.models.flight import FlightOption


def build_select_flight_prompt(flight: FlightOption) -> str:
    return f"Click the 'Select Flight' button for the {flight.airline} {flight.flight_number} flight"


def build_passenger_prompt(passenger: PassengerInfo, index: int, is_primary: bool) -> str:
    base = (
        f"Fill in passenger {index + 1}: first name '{passenger.first_name}', "
        f"last name '{passenger.last_name}', date of birth '{passenger.date_of_birth}'"
    )
    if is_primary:
        return base + f", email '{passenger.email}', phone '{passenger.phone}'"
    return base


def build_booking_audit_entry(
    booking_id: str,
    employee_id: str,
    confirmation: BookingConfirmation | None,
    fallback_url_set: bool,
    warnings: list[str],
    latency_ms: float,
) -> dict[str, Any]:
    return {
        "auditId": f"flight-booking-{uuid4()}",
        "bookingId": booking_id,
        "employeeId": employee_id,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "flight_booking",
        "output": {
            "booking_reference": confirmation.booking_reference if confirmation else None,
            "total_amount": confirmation.total_amount if confirmation else None,
            "fallback_url_set": fallback_url_set,
            "warnings": warnings,
        },
        "latency_ms": latency_ms,
    }
