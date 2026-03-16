from pydantic import BaseModel, Field

from core.models.booking import BookingPlan


class FlightOption(BaseModel):
    airline: str = Field(..., description="Airline name")
    flight_number: str = Field(..., description="Flight number (e.g., DL123)")
    price: float = Field(..., gt=0, description="Price in USD")
    departure_time: str = Field(..., description="Departure time (e.g., 08:00 AM)")
    arrival_time: str = Field(..., description="Arrival time (e.g., 11:30 AM)")
    stops: int = Field(..., ge=0, description="Number of stops")
    cabin_class: str = Field(..., description="Cabin class")
    duration: str | None = Field(None, description="Flight duration (e.g., 3h 30m)")


class FlightSearchResult(BaseModel):
    flights: list[FlightOption] = Field(..., description="List of flight options")
    search_origin: str = Field(..., description="Origin airport code")
    search_destination: str = Field(..., description="Destination airport code")
    search_date: str = Field(..., description="Search date")
    total_results: int = Field(..., ge=0, description="Total number of results found")


class FlightSearchInput(BaseModel):
    booking_id: str
    employee_id: str
    booking_plan: BookingPlan


class FlightSearchOutput(BaseModel):
    booking_id: str
    employee_id: str
    search_result: FlightSearchResult
    fallback_url: str | None = None
    warnings: list[str] = []
