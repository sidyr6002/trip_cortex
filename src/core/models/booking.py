from datetime import date
from typing import TYPE_CHECKING, Literal

from dateutil import parser as dateutil_parser
from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    from core.models.flight import FlightOption


def _coerce_date(v: object) -> object:
    """Coerce common date string formats to date objects."""
    if isinstance(v, date) or not isinstance(v, str):
        return v
    try:
        return dateutil_parser.parse(v).date()
    except (ValueError, TypeError):
        return v


class PolicySource(BaseModel):
    chunk_id: str
    section_title: str
    page: int
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class BookingParameters(BaseModel):
    origin: str = Field(..., min_length=3, max_length=4)
    destination: str = Field(..., min_length=3, max_length=4)
    departure_date: date
    return_date: date | None = None
    cabin_class: str = Field(..., pattern="^(economy|premium_economy|business|first)$")
    time_preference: str | None = None
    passenger_count: int = Field(default=1, ge=1, le=9)

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def normalize_airport_code(cls, v: str) -> str:
        if v is None:
            raise ValueError("airport code must not be null")
        return v.strip().upper()

    @field_validator("departure_date", "return_date", mode="before")
    @classmethod
    def coerce_date_format(cls, v: object) -> object:
        return _coerce_date(v)

    @field_validator("departure_date")
    @classmethod
    def departure_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("departure_date must not be in the past")
        return v

    @field_validator("cabin_class", mode="before")
    @classmethod
    def normalize_cabin_class(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def return_after_departure(self) -> "BookingParameters":
        if self.return_date and self.return_date <= self.departure_date:
            raise ValueError("return_date must be after departure_date")
        if self.origin == self.destination:
            raise ValueError("origin and destination must be different")
        return self


class PolicyConstraints(BaseModel):
    max_budget_usd: float = Field(..., gt=0, le=50_000)
    preferred_vendors: list[str]
    advance_booking_days_required: int | None = None
    advance_booking_met: bool
    requires_approval: bool = False
    approval_reason: str | None = None

    @field_validator("preferred_vendors")
    @classmethod
    def vendors_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("preferred_vendors must contain at least one vendor")
        return v

    @model_validator(mode="after")
    def approval_reason_required(self) -> "PolicyConstraints":
        if self.requires_approval and self.approval_reason is None:
            raise ValueError("approval_reason is required when requires_approval is True")
        return self


class ReasoningRequest(BaseModel):
    booking_id: str = Field(min_length=1)
    employee_id: str = Field(min_length=1)
    user_query: str = Field(min_length=1, max_length=10_000)
    context_text: str
    confidence_level: Literal["high", "low", "none"]
    max_similarity: float = Field(ge=0.0, le=1.0)


class BookingPlan(BaseModel):
    intent: str = Field(..., pattern="^(flight_booking|flight_search|policy_query)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    parameters: BookingParameters
    policy_constraints: PolicyConstraints
    policy_sources: list[PolicySource]
    reasoning_summary: str
    warnings: list[str] = []
    fallback_url: str | None = None

    @classmethod
    def strict_defaults(
        cls,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
    ) -> "BookingPlan":
        return cls(
            intent="flight_booking",
            confidence=0.0,
            parameters=BookingParameters(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                cabin_class="economy",
                passenger_count=1,
            ),
            policy_constraints=PolicyConstraints(
                max_budget_usd=300.0,
                preferred_vendors=["any"],
                advance_booking_days_required=14,
                advance_booking_met=False,
                requires_approval=True,
                approval_reason="Auto-generated strict defaults — LLM validation failed",
            ),
            policy_sources=[],
            reasoning_summary="Strict defaults applied — reasoning output failed validation after retries.",
            warnings=["STRICT_DEFAULTS_APPLIED"],
        )


ThinkingEffort = Literal["low", "medium", "high"]


class ReasoningResult(BaseModel):
    booking_id: str
    employee_id: str
    plan: BookingPlan
    model_id: str
    thinking_effort: ThinkingEffort
    latency_ms: float = Field(ge=0.0)
    retry_count: int = Field(default=0, ge=0)
    escalated: bool = False
    parse_failed: bool = False


class PassengerInfo(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # DD-MM-YYYY format (portal expects this)
    email: str | None = None
    phone: str | None = None


class BookingInput(BaseModel):
    booking_id: str
    employee_id: str
    flight: "FlightOption"
    booking_plan: BookingPlan
    passengers: list[PassengerInfo]
    search_url: str  # search results URL — workflow navigates here first, then clicks "Select Flight"


class BookingConfirmation(BaseModel):
    booking_reference: str = Field(..., description="Booking reference e.g. FS-SG8194-ABC123")
    payment_reference: str | None = Field(None, description="Stripe payment intent ID")
    total_amount: float = Field(..., gt=0, description="Total amount paid in USD")
    flight_number: str = Field(..., description="Flight number from confirmation")


class BookingOutput(BaseModel):
    booking_id: str
    employee_id: str
    confirmation: BookingConfirmation | None = None
    fallback_url: str | None = None
    warnings: list[str] = []
