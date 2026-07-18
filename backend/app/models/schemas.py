from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    preferred_flight_times: str | None = None
    avoid_layovers: bool = False
    activity_interests: list[str] = Field(default_factory=list)
    hotel_style: str | None = None
    default_travelers: int = 1
    trip_styles: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TripRequest(BaseModel):
    session_id: str = "default"
    origin: str | None = None
    origin_airport: str | None = None
    budget: float | None = None
    duration_days: int = 3
    travelers: int = 1
    trip_style: str | None = None
    departure_date: str | None = None
    return_date: str | None = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class ListingItem(BaseModel):
    category: Literal["flight", "hotel", "car"]
    title: str
    description: str
    price: float
    currency: str = "USD"
    details: dict[str, Any] = Field(default_factory=dict)


class WeatherInfo(BaseModel):
    summary: str
    high_f: float | None = None
    low_f: float | None = None
    precipitation_chance: float | None = None
    alerts: list[str] = Field(default_factory=list)


class TripOption(BaseModel):
    id: str
    destination_city: str
    destination_state: str | None = None
    destination_airport: str
    destination_lat: float
    destination_lng: float
    origin_airport: str
    total_price: float
    currency: str = "USD"
    flight_price: float
    hotel_price: float
    car_price: float
    listings: list[ListingItem]
    why: list[str] = Field(default_factory=list)
    weather: WeatherInfo | None = None
    departure_date: str | None = None
    return_date: str | None = None


class TripPlanResponse(BaseModel):
    session_id: str
    options: list[TripOption]
    message: str
    preferences_used: UserPreferences


class AgentQueryRequest(BaseModel):
    query: str
    session_id: str = "default"
    turn_id: str | None = None


class AgentQueryResponse(BaseModel):
    response: str
    action: str | None = None
    payload: dict[str, Any] | None = None


class SelectTripRequest(BaseModel):
    session_id: str = "default"
    option_id: str


class RecommendationsResponse(BaseModel):
    option_id: str
    destination: str
    packing: list[str]
    tips: list[str]
    weather_notes: list[str]
    itinerary_highlights: list[str]
