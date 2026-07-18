"""Gemini-backed day-trip planner.

When a user selects a trip and taps "Plan day trip", we ask Gemini (with
Google Search grounding) to build a real, current day-by-day plan for the
destination. The model returns structured JSON with a latitude/longitude for
every stop so the frontend can drop pins and draw arrows between them.

If no Gemini key is configured, or the call/parse fails, we fall back to a
simple generic plan placed around the city center so the map still renders.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import date, timedelta

from app.config import get_settings
from app.models.schemas import (
    Activity,
    Itinerary,
    ItineraryDay,
    ItinerarySegment,
    TripOption,
)

logger = logging.getLogger(__name__)


class DayPlanError(Exception):
    """Raised when a day plan could not be generated from Gemini."""


PERIODS = ["Morning", "Afternoon", "Evening"]
DEFAULT_TIMES = {"Morning": "9:00 AM", "Afternoon": "1:00 PM", "Evening": "7:00 PM"}


def _num_days(option: TripOption) -> int:
    if option.departure_date and option.return_date:
        try:
            start = date.fromisoformat(option.departure_date)
            end = date.fromisoformat(option.return_date)
            return max(1, min(5, (end - start).days + 1))
        except ValueError:
            pass
    return 3


def _dates(option: TripOption) -> date | None:
    if option.departure_date:
        try:
            return date.fromisoformat(option.departure_date)
        except ValueError:
            return None
    return None


def _build_prompt(option: TripOption, style: str | None, num_days: int) -> str:
    where = option.destination_city
    if option.destination_state:
        where += f", {option.destination_state}"
    style_line = f"The traveler is into: {style}." if style else ""
    return (
        f"Plan a realistic {num_days}-day trip in {where}. {style_line}\n"
        "Use current, real, well-reviewed places (restaurants, sights, parks, nightlife). "
        "For each day give exactly three stops: one Morning, one Afternoon, one Evening. "
        "Order stops so they flow geographically to minimize backtracking.\n\n"
        "Return ONLY valid JSON (no markdown, no commentary) in exactly this shape:\n"
        "{\n"
        '  "days": [\n'
        "    {\n"
        '      "day": 1,\n'
        '      "segments": [\n'
        '        {"period": "Morning", "time": "9:00 AM", "name": "Place name", '
        '"category": "cafe|food|sightseeing|outdoor|museum|shopping|nightlife|beach", '
        '"description": "one short sentence", "lat": 0.0, "lng": 0.0, "cost": 0}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "The lat and lng must be accurate decimal coordinates for each real place. "
        "cost is an approximate per-person USD amount (0 if free)."
    )


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    # Strip code fences if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _coerce_period(value: str, fallback: str) -> str:
    v = (value or "").strip().capitalize()
    return v if v in PERIODS else fallback


def _itinerary_from_json(option: TripOption, data: dict) -> Itinerary:
    start_date = _dates(option)
    days: list[ItineraryDay] = []
    all_activities: list[Activity] = []

    raw_days = data.get("days") or []
    for idx, raw_day in enumerate(raw_days[:5]):
        segments: list[ItinerarySegment] = []
        raw_segments = raw_day.get("segments") or []
        for seg_idx, seg in enumerate(raw_segments):
            fallback_period = PERIODS[min(seg_idx, len(PERIODS) - 1)]
            period = _coerce_period(seg.get("period", ""), fallback_period)
            try:
                lat = float(seg.get("lat"))
                lng = float(seg.get("lng"))
            except (TypeError, ValueError):
                lat, lng = option.destination_lat, option.destination_lng
            activity = Activity(
                id=str(uuid.uuid4())[:8],
                name=str(seg.get("name") or "Local stop"),
                category=str(seg.get("category") or "sightseeing"),
                description=str(seg.get("description") or ""),
                lat=lat,
                lng=lng,
                cost_estimate=float(seg.get("cost") or 0),
            )
            all_activities.append(activity)
            segments.append(
                ItinerarySegment(
                    period=period,  # type: ignore[arg-type]
                    time_label=str(seg.get("time") or DEFAULT_TIMES[period]),
                    activity=activity,
                )
            )

        day_date = None
        title = f"Day {idx + 1}"
        if start_date:
            current = start_date + timedelta(days=idx)
            day_date = current.isoformat()
            title = f"Day {idx + 1} · {current.strftime('%a, %b %d')}"
        days.append(ItineraryDay(day_index=idx + 1, date=day_date, title=title, segments=segments))

    return Itinerary(
        option_id=option.id,
        destination_city=option.destination_city,
        destination_state=option.destination_state,
        days=days,
        activities=all_activities,
    )


async def generate_day_plan(option: TripOption, style: str | None = None) -> Itinerary:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise DayPlanError("GEMINI_API_KEY is not configured.")

    num_days = _num_days(option)
    prompt = _build_prompt(option, style, num_days)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.7,
            ),
        )
    except Exception as exc:
        logger.warning("Gemini day plan request failed: %s", exc)
        raise DayPlanError("The day-plan service is temporarily unavailable.") from exc

    data = _extract_json(response.text or "")
    if not data:
        raise DayPlanError("Could not read a day plan from the model response.")

    itinerary = _itinerary_from_json(option, data)
    if not itinerary.days:
        raise DayPlanError("The model did not return any activities.")
    return itinerary
