from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

CITY_COORDS = {
    "austin": (30.2672, -97.7431),
    "denver": (39.7392, -104.9903),
    "nashville": (36.1627, -86.7816),
    "san diego": (32.7157, -117.1611),
    "portland": (45.5152, -122.6784),
    "miami": (25.7617, -80.1918),
    "phoenix": (33.4484, -112.0740),
    "seattle": (47.6062, -122.3321),
}


async def get_weather(city: str, state: str | None = None) -> dict:
    key = city.lower()
    lat, lng = CITY_COORDS.get(key, (39.8283, -98.5795))

    if key not in CITY_COORDS:
        try:
            query = f"{city},{state or 'US'}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                geo = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": query, "count": 1, "language": "en", "format": "json"},
                )
                geo.raise_for_status()
                results = geo.json().get("results") or []
                if results:
                    lat = results[0]["latitude"]
                    lng = results[0]["longitude"]
        except Exception as exc:
            logger.warning("Geocoding failed for %s: %s", city, exc)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            forecast = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
                    "temperature_unit": "fahrenheit",
                    "timezone": "auto",
                    "forecast_days": 3,
                },
            )
            forecast.raise_for_status()
            data = forecast.json()
            daily = data.get("daily", {})
            highs = daily.get("temperature_2m_max") or [75]
            lows = daily.get("temperature_2m_min") or [55]
            precip = daily.get("precipitation_probability_max") or [10]
            high = highs[0]
            low = lows[0]
            rain_chance = precip[0]

            summary_parts = [f"{city} will be around {round(high)}°F"]
            alerts: list[str] = []

            if high >= 95:
                alerts.append("Extreme heat — hiking may not be ideal; bring sunscreen and stay hydrated.")
            elif high >= 85:
                alerts.append("Warm weather — pack light clothing and sunscreen.")
            elif low <= 32:
                alerts.append("Cold snap possible — bring warm layers.")
            elif rain_chance >= 60:
                alerts.append("Rain likely — pack a rain jacket and plan indoor backup activities.")
            elif rain_chance <= 20 and high <= 80:
                alerts.append("Clear weather — great for outdoor activities.")

            if not alerts:
                alerts.append("Comfortable conditions for sightseeing.")

            return {
                "summary": ". ".join(summary_parts) + ". " + alerts[0],
                "high_f": float(high),
                "low_f": float(low),
                "precipitation_chance": float(rain_chance),
                "alerts": alerts,
            }
    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return {
            "summary": f"Weather data unavailable for {city}. Check local forecast before packing.",
            "high_f": None,
            "low_f": None,
            "precipitation_chance": None,
            "alerts": ["Check the forecast closer to departure."],
        }
