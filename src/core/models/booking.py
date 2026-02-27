from datetime import date

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def return_after_departure(self) -> "BookingParameters":
        if self.return_date and self.return_date <= self.departure_date:
            raise ValueError("return_date must be after departure_date")
        return self


class PolicyConstraints(BaseModel):
    max_budget_usd: float = Field(..., gt=0)
    preferred_vendors: list[str]
    advance_booking_days_required: int | None = None
    advance_booking_met: bool
    requires_approval: bool = False
    approval_reason: str | None = None


class BookingPlan(BaseModel):
    intent: str = Field(..., pattern="^(flight_booking|flight_search|policy_query)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    parameters: BookingParameters
    policy_constraints: PolicyConstraints
    policy_sources: list[PolicySource]
    reasoning_summary: str
    warnings: list[str] = []
    fallback_url: str | None = None
