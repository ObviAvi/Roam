from __future__ import annotations

import re
import uuid

from app.models.schemas import (
    ListingItem,
    RecommendationsResponse,
    TripOption,
    TripPlanResponse,
    TripRequest,
    WeatherInfo,
)
from app.services.memory import get_session_request, merge_trip_request, save_session_options
from app.services.sabre import SabreClient
from app.services.weather import get_weather


def _extract_budget(text: str) -> float | None:
    patterns = [
        r"(?:\$|usd\s*)?(\d{2,5})\s*(?:dollar|usd|budget|total|per person)?",
        r"budget\s*(?:of|is|:|-)?\s*\$?(\d{2,5})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.replace(",", ""), re.I)
        if match:
            return float(match.group(1))
    return None


def _extract_travelers(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(people|travelers|guests|of us|persons?)", text, re.I)
    if match:
        return int(match.group(1))
    if "couple" in text.lower() or "two of us" in text.lower():
        return 2
    if "solo" in text.lower() or "just me" in text.lower():
        return 1
    return None


def _extract_origin(text: str) -> str | None:
    patterns = [
        r"(?:from|leaving|departing|based in|live in|starting from)\s+([A-Za-z .]+?)(?:\.|,|$|\s+for|\s+with|\s+on|\s+budget)",
        r"^([A-Za-z .]{3,30})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            origin = match.group(1).strip()
            if origin.lower() not in {"a", "the", "my", "our", "trip", "weekend"}:
                return origin
    return None


def _extract_style(text: str) -> str | None:
    styles = [
        "adventure",
        "relaxation",
        "food",
        "nightlife",
        "beach",
        "outdoor",
        "music",
        "city",
        "culture",
    ]
    lower = text.lower()
    for style in styles:
        if style in lower:
            return style
    return None


def parse_user_message(message: str, session_id: str) -> TripRequest:
    current = get_session_request(session_id)
    updates = TripRequest(session_id=session_id)

    budget = _extract_budget(message)
    if budget:
        updates.budget = budget

    travelers = _extract_travelers(message)
    if travelers:
        updates.travelers = travelers

    origin = _extract_origin(message)
    if origin:
        updates.origin = origin

    style = _extract_style(message)
    if style:
        updates.trip_style = style
        updates.preferences.trip_styles = [style]

    if "morning flight" in message.lower():
        updates.preferences.preferred_flight_times = "morning"
    if "no layover" in message.lower() or "direct flight" in message.lower():
        updates.preferences.avoid_layovers = True
    if "boutique hotel" in message.lower():
        updates.preferences.hotel_style = "boutique"

    merged = merge_trip_request(session_id, updates)
    if not merged.origin and current.origin:
        merged.origin = current.origin
    if not merged.budget and current.budget:
        merged.budget = current.budget
    if merged.travelers == 1 and current.travelers > 1:
        merged.travelers = current.travelers
    return merged


def _within_budget(total: float, budget: float | None) -> bool:
    if not budget:
        return True
    return total <= budget * 1.05


async def build_trip_plan(request: TripRequest) -> TripPlanResponse:
    sabre = SabreClient()
    origin_airport = sabre.resolve_airport(request.origin_airport or request.origin)
    departure, return_date = request.departure_date, request.return_date
    if not departure or not return_date:
        departure, return_date = SabreClient.next_weekend()

    destinations = sabre.pick_destinations(origin_airport, request.trip_style, count=3)
    options: list[TripOption] = []

    for dest in destinations:
        flight = await sabre.search_flights(
            origin_airport,
            dest["airport"],
            departure,
            return_date,
            request.travelers,
        )
        hotel = await sabre.search_hotels(
            dest["airport"],
            dest["city"],
            departure,
            return_date,
            request.travelers,
        )
        car = await sabre.search_cars(dest["airport"], departure, return_date)
        total = round(flight["price"] + hotel["price"] + car["price"], 2)

        if not _within_budget(total, request.budget):
            continue

        weather_data = await get_weather(dest["city"], dest.get("state"))
        weather = WeatherInfo(**weather_data)

        why = list(dest["why"])
        if request.trip_style:
            why.insert(0, f"Matches your {request.trip_style} travel style")
        if request.budget:
            why.append(f"Fits your ${int(request.budget)} budget at ${total:.0f} total")
        why.append(weather.summary)

        option = TripOption(
            id=str(uuid.uuid4())[:8],
            destination_city=dest["city"],
            destination_state=dest.get("state"),
            destination_airport=dest["airport"],
            destination_lat=dest["lat"],
            destination_lng=dest["lng"],
            origin_airport=origin_airport,
            total_price=total,
            flight_price=flight["price"],
            hotel_price=hotel["price"],
            car_price=car["price"],
            listings=[
                ListingItem(category="flight", title=flight["title"], description=flight["description"], price=flight["price"], details=flight["details"]),
                ListingItem(category="hotel", title=hotel["title"], description=hotel["description"], price=hotel["price"], details=hotel["details"]),
                ListingItem(category="car", title=car["title"], description=car["description"], price=car["price"], details=car["details"]),
            ],
            why=why,
            weather=weather,
            departure_date=departure,
            return_date=return_date,
        )
        options.append(option)

    if not options and destinations:
        dest = destinations[0]
        flight = await sabre.search_flights(origin_airport, dest["airport"], departure, return_date, request.travelers)
        hotel = await sabre.search_hotels(dest["airport"], dest["city"], departure, return_date, request.travelers)
        car = await sabre.search_cars(dest["airport"], departure, return_date)
        total = round(flight["price"] + hotel["price"] + car["price"], 2)
        weather_data = await get_weather(dest["city"], dest.get("state"))
        option = TripOption(
            id=str(uuid.uuid4())[:8],
            destination_city=dest["city"],
            destination_state=dest.get("state"),
            destination_airport=dest["airport"],
            destination_lat=dest["lat"],
            destination_lng=dest["lng"],
            origin_airport=origin_airport,
            total_price=total,
            flight_price=flight["price"],
            hotel_price=hotel["price"],
            car_price=car["price"],
            listings=[
                ListingItem(category="flight", title=flight["title"], description=flight["description"], price=flight["price"], details=flight["details"]),
                ListingItem(category="hotel", title=hotel["title"], description=hotel["description"], price=hotel["price"], details=hotel["details"]),
                ListingItem(category="car", title=car["title"], description=car["description"], price=car["price"], details=car["details"]),
            ],
            why=dest["why"] + [weather_data["summary"]],
            weather=WeatherInfo(**weather_data),
            departure_date=departure,
            return_date=return_date,
        )
        options = [option]

    options.sort(key=lambda o: o.total_price)
    save_session_options(request.session_id, [o.model_dump() for o in options])

    if not options:
        message = "I couldn't find trip options with those constraints. Try raising your budget or changing your origin."
    else:
        lines = [f"I found {len(options)} complete weekend trip options:"]
        for idx, opt in enumerate(options, start=1):
            lines.append(
                f"Option {idx}: {opt.destination_city}, {opt.destination_state or ''} — "
                f"flights ${opt.flight_price:.0f}, hotel ${opt.hotel_price:.0f}, car ${opt.car_price:.0f}, "
                f"total ${opt.total_price:.0f}."
            )
        message = " ".join(lines)

    return TripPlanResponse(
        session_id=request.session_id,
        options=options,
        message=message,
        preferences_used=request.preferences,
    )


def build_recommendations(option: dict) -> RecommendationsResponse:
    city = option.get("destination_city", "your destination")
    weather = option.get("weather") or {}
    alerts = weather.get("alerts") or []
    style_notes = option.get("why") or []

    packing = [
        "Comfortable walking shoes",
        "Phone charger and portable battery",
        "Travel documents and ID",
    ]
    if weather.get("high_f") and weather["high_f"] >= 85:
        packing.extend(["Sunscreen", "Light breathable clothing", "Reusable water bottle"])
    if weather.get("low_f") and weather["low_f"] <= 45:
        packing.extend(["Warm jacket", "Layers for cool evenings"])
    if weather.get("precipitation_chance") and weather["precipitation_chance"] >= 50:
        packing.append("Compact umbrella or rain jacket")

    tips = [
        "Confirm flight and hotel details 24 hours before departure.",
        "Save offline maps for your destination.",
        "Set a daily spending buffer for meals and activities.",
    ]
    tips.extend(style_notes[:2])

    return RecommendationsResponse(
        option_id=option.get("id", ""),
        destination=city,
        packing=packing,
        tips=tips,
        weather_notes=alerts,
        itinerary_highlights=[
            f"Fly {option.get('origin_airport')} → {option.get('destination_airport')}",
            f"Stay at {next((l['title'] for l in option.get('listings', []) if l.get('category') == 'hotel'), 'your hotel')}",
            f"Explore {city} with your rental car",
        ],
    )


def missing_fields(request: TripRequest) -> list[str]:
    missing = []
    if not request.origin and not request.origin_airport:
        missing.append("starting city or airport")
    if not request.budget:
        missing.append("budget")
    return missing
