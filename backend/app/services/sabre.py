from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Sabre often returns monetary amounts as fixed-point integers (e.g. 46347 = $463.47).
_PRICE_CAPS = {
    "flight": 3500.0,
    "hotel": 2500.0,
    "car": 800.0,
}


def normalize_sabre_price(raw: float, category: str = "generic") -> float:
    if raw <= 0:
        return 0.0

    cap = _PRICE_CAPS.get(category, 5000.0)
    value = float(raw)

    if value > cap:
        scaled = value / 100.0
        if scaled <= cap:
            return round(scaled, 2)

    return round(value, 2)


def _extract_flight_price(pricing: dict[str, Any]) -> float | None:
    fare = pricing.get("fare", {})
    total_fare = fare.get("totalFare", {})

    candidates: list[float] = []
    for key in ("totalPrice", "equivalentAmount", "baseFareAmount"):
        value = total_fare.get(key)
        if value is not None:
            candidates.append(float(value))

    passenger_list = pricing.get("passengerInfoList") or []
    for passenger in passenger_list:
        info = passenger.get("passengerInfo", passenger)
        for key in ("totalFare", "equivalentTotalFare"):
            block = info.get(key, {})
            for amount_key in ("amount", "totalPrice", "equivalentAmount"):
                value = block.get(amount_key)
                if value is not None:
                    candidates.append(float(value))

    if not candidates:
        return None

    normalized = [normalize_sabre_price(value, "flight") for value in candidates]
    return min(normalized)

DESTINATIONS = [
    {
        "city": "Austin",
        "state": "TX",
        "airport": "AUS",
        "lat": 30.2672,
        "lng": -97.7431,
        "styles": ["food", "nightlife", "music", "city"],
        "why": ["Great food scene", "Live music capital", "Warm weather"],
    },
    {
        "city": "Denver",
        "state": "CO",
        "airport": "DEN",
        "lat": 39.7392,
        "lng": -104.9903,
        "styles": ["adventure", "outdoor", "city"],
        "why": ["Mountain access", "Craft breweries", "Outdoor activities"],
    },
    {
        "city": "Nashville",
        "state": "TN",
        "airport": "BNA",
        "lat": 36.1627,
        "lng": -86.7816,
        "styles": ["music", "food", "nightlife"],
        "why": ["Live music", "Southern food", "Vibrant nightlife"],
    },
    {
        "city": "San Diego",
        "state": "CA",
        "airport": "SAN",
        "lat": 32.7157,
        "lng": -117.1611,
        "styles": ["beach", "relaxation", "food"],
        "why": ["Beach weather", "Relaxed vibe", "Great tacos"],
    },
    {
        "city": "Portland",
        "state": "OR",
        "airport": "PDX",
        "lat": 45.5152,
        "lng": -122.6784,
        "styles": ["food", "outdoor", "city"],
        "why": ["Food trucks", "Craft coffee", "Nearby nature"],
    },
    {
        "city": "Miami",
        "state": "FL",
        "airport": "MIA",
        "lat": 25.7617,
        "lng": -80.1918,
        "styles": ["beach", "nightlife", "food"],
        "why": ["Beach access", "Latin cuisine", "Nightlife"],
    },
]

CITY_TO_AIRPORT = {
    "new york": "JFK",
    "nyc": "JFK",
    "los angeles": "LAX",
    "la": "LAX",
    "chicago": "ORD",
    "san francisco": "SFO",
    "sf": "SFO",
    "seattle": "SEA",
    "boston": "BOS",
    "atlanta": "ATL",
    "dallas": "DFW",
    "houston": "IAH",
    "phoenix": "PHX",
    "las vegas": "LAS",
    "vegas": "LAS",
    "washington": "DCA",
    "dc": "DCA",
}


class SabreClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.sabre_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.settings.sabre_base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, headers=self._headers(), json=payload)
                if response.status_code >= 400:
                    logger.warning("Sabre %s failed: %s %s", path, response.status_code, response.text[:500])
                    return None
                return response.json()
        except Exception as exc:
            logger.warning("Sabre request error on %s: %s", path, exc)
            return None

    def resolve_airport(self, location: str | None) -> str:
        if not location:
            return "LAX"
        cleaned = location.strip().upper()
        if len(cleaned) == 3 and cleaned.isalpha():
            return cleaned
        lower = location.strip().lower()
        return CITY_TO_AIRPORT.get(lower, "LAX")

    def pick_destinations(self, origin: str, style: str | None, count: int = 3) -> list[dict]:
        origin_airport = self.resolve_airport(origin)
        style_lower = (style or "").lower()
        scored = []
        for dest in DESTINATIONS:
            if dest["airport"] == origin_airport:
                continue
            score = 0
            if style_lower:
                score += sum(1 for s in dest["styles"] if style_lower in s or s in style_lower)
            scored.append((score, dest))
        scored.sort(key=lambda item: item[0], reverse=True)
        chosen = [item[1] for item in scored[:count]]
        if len(chosen) < count:
            for dest in DESTINATIONS:
                if dest not in chosen and dest["airport"] != origin_airport:
                    chosen.append(dest)
                if len(chosen) >= count:
                    break
        return chosen

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str,
        travelers: int = 1,
    ) -> dict[str, Any]:
        payload = {
            "OTA_AirLowFareSearchRQ": {
                "Version": "5",
                "POS": {
                    "Source": [
                        {
                            "PseudoCityCode": "WN3K",
                            "RequestorID": {
                                "Type": "1",
                                "ID": "1",
                                "CompanyName": {"Code": "TN"},
                            },
                        }
                    ]
                },
                "OriginDestinationInformation": [
                    {
                        "DepartureDateTime": f"{departure_date}T10:00:00",
                        "OriginLocation": {"LocationCode": origin},
                        "DestinationLocation": {"LocationCode": destination},
                    },
                    {
                        "DepartureDateTime": f"{return_date}T14:00:00",
                        "OriginLocation": {"LocationCode": destination},
                        "DestinationLocation": {"LocationCode": origin},
                    },
                ],
                "TravelPreferences": {
                    "TPA_Extensions": {
                        "NumTrips": {"Number": 5},
                    }
                },
                "TravelerInfoSummary": {
                    "SeatsRequested": [travelers],
                    "AirTravelerAvail": [
                        {
                            "PassengerTypeQuantity": [
                                {"Code": "ADT", "Quantity": travelers},
                            ]
                        }
                    ],
                },
                "TPA_Extensions": {
                    "IntelliSellTransaction": {
                        "RequestType": {"Name": "50ITINS"},
                    }
                },
            }
        }

        data = await self._post("/v5/offers/shop", payload)
        if not data:
            return self._fallback_flight(origin, destination, travelers)

        return self._parse_flight_response(data, origin, destination, travelers)

    def _fallback_flight(self, origin: str, destination: str, travelers: int) -> dict[str, Any]:
        base = 120 + (hash(origin + destination) % 180)
        price = round(base * travelers, 2)
        return {
            "price": price,
            "currency": "USD",
            "title": f"Round-trip {origin} ↔ {destination}",
            "description": f"Economy round-trip for {travelers} traveler(s)",
            "details": {
                "origin": origin,
                "destination": destination,
                "airline": "Sample Air",
                "stops": "Nonstop",
                "source": "estimate",
            },
        }

    def _parse_flight_response(
        self,
        data: dict[str, Any],
        origin: str,
        destination: str,
        travelers: int,
    ) -> dict[str, Any]:
        grouped = data.get("groupedItineraryResponse", {})
        stats = grouped.get("statistics", {})
        itineraries = grouped.get("itineraryGroups", [])
        best_price = None
        best_desc = "Round-trip flight"
        airline = "Multiple carriers"
        stops = "Varies"

        if stats.get("itineraryCount", 0) == 0:
            return self._fallback_flight(origin, destination, travelers)

        for group in itineraries:
            for itinerary in group.get("itineraries", []):
                pricing_list = itinerary.get("pricingInformation") or [{}]
                total = _extract_flight_price(pricing_list[0])
                if total is not None and (best_price is None or total < best_price):
                    best_price = total
                    legs = itinerary.get("legs", [])
                    if legs:
                        refs = legs[0].get("ref", 0)
                        schedules = grouped.get("scheduleDescs", [])
                        if refs < len(schedules):
                            carrier = schedules[refs].get("carrier", {})
                            airline = carrier.get("marketing", airline)
                            stops = "Nonstop" if len(legs) <= 2 else f"{len(legs)-1} stop(s)"

        if best_price is None:
            return self._fallback_flight(origin, destination, travelers)

        return {
            "price": round(best_price, 2),
            "currency": "USD",
            "title": f"Round-trip {origin} ↔ {destination}",
            "description": f"{airline} · {stops} · {travelers} traveler(s)",
            "details": {
                "origin": origin,
                "destination": destination,
                "airline": airline,
                "stops": stops,
                "source": "sabre",
            },
        }

    async def search_hotels(
        self,
        destination_airport: str,
        city: str,
        check_in: str,
        check_out: str,
        travelers: int = 1,
    ) -> dict[str, Any]:
        payload = {
            "GetHotelAvailRQ": {
                "SearchCriteria": {
                    "OffSet": 1,
                    "PageSize": 5,
                    "SortBy": "TotalRate",
                    "SortOrder": "ASC",
                    "TierLabels": False,
                    "RateDetailsInd": True,
                    "HotelRefs": {"HotelRef": [{"HotelCityCode": destination_airport[:3]}]},
                    "RateInfoRef": {
                        "ConvertedRateInfoOnly": True,
                        "CurrencyCode": "USD",
                        "BestOnly": "1",
                        "StayDateTimeRange": {
                            "StartDate": check_in,
                            "EndDate": check_out,
                        },
                        "Rooms": {
                            "Room": [
                                {
                                    "Index": 1,
                                    "Adults": travelers,
                                }
                            ]
                        },
                    },
                }
            }
        }

        data = await self._post("/v4.1.0/hotel/avail", payload)
        if not data:
            return self._fallback_hotel(city, check_in, check_out, travelers)

        return self._parse_hotel_response(data, city, check_in, check_out, travelers)

    def _fallback_hotel(self, city: str, check_in: str, check_out: str, travelers: int) -> dict[str, Any]:
        nights = max(1, (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days)
        nightly = 95 + (hash(city) % 80)
        total = round(nightly * nights, 2)
        return {
            "price": total,
            "currency": "USD",
            "title": f"{city} Boutique Hotel",
            "description": f"{nights} night(s) · {travelers} guest(s) · Free cancellation",
            "details": {
                "nights": nights,
                "rating": "4.2",
                "source": "estimate",
            },
        }

    def _parse_hotel_response(
        self,
        data: dict[str, Any],
        city: str,
        check_in: str,
        check_out: str,
        travelers: int,
    ) -> dict[str, Any]:
        hotels = data.get("GetHotelAvailRS", {}).get("HotelAvailInfos", {}).get("HotelAvailInfo", [])
        if not hotels:
            return self._fallback_hotel(city, check_in, check_out, travelers)

        hotel = hotels[0]
        name = hotel.get("HotelInfo", {}).get("HotelName", f"{city} Hotel")
        rate = hotel.get("HotelRateInfo", {}).get("RateInfos", {}).get("ConvertedRateInfo", [{}])[0]
        total = normalize_sabre_price(
            float(rate.get("AmountAfterTax", 0) or rate.get("AverageNightlyRate", 0) or 0),
            "hotel",
        )
        if total <= 0:
            return self._fallback_hotel(city, check_in, check_out, travelers)

        nights = max(1, (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days)
        return {
            "price": round(total, 2),
            "currency": "USD",
            "title": name,
            "description": f"{nights} night(s) · {travelers} guest(s)",
            "details": {
                "nights": nights,
                "rating": hotel.get("HotelInfo", {}).get("SabreRating", "N/A"),
                "source": "sabre",
            },
        }

    async def search_cars(
        self,
        destination_airport: str,
        pick_up: str,
        drop_off: str,
    ) -> dict[str, Any]:
        payload = {
            "GetVehAvailRQ": {
                "SearchCriteria": {
                    "PickUpDate": pick_up,
                    "PickUpTime": "10:00",
                    "ReturnDate": drop_off,
                    "ReturnTime": "10:00",
                    "PickUpLocation": {"LocationCode": destination_airport},
                    "ReturnLocation": {"LocationCode": destination_airport},
                    "VendorPrefs": {"VendorPref": [{"Code": "ZE"}, {"Code": "ET"}]},
                }
            }
        }

        data = await self._post("/v2.0/veh/avail", payload)
        if not data:
            return self._fallback_car(destination_airport, pick_up, drop_off)

        return self._parse_car_response(data, destination_airport, pick_up, drop_off)

    def _fallback_car(self, airport: str, pick_up: str, drop_off: str) -> dict[str, Any]:
        days = max(1, (date.fromisoformat(drop_off) - date.fromisoformat(pick_up)).days)
        total = round(35 * days + (hash(airport) % 25), 2)
        return {
            "price": total,
            "currency": "USD",
            "title": "Compact rental car",
            "description": f"{days} day(s) · Unlimited mileage · Airport pickup",
            "details": {
                "vendor": "Major rental brand",
                "class": "Compact",
                "source": "estimate",
            },
        }

    def _parse_car_response(self, data: dict[str, Any], airport: str, pick_up: str, drop_off: str) -> dict[str, Any]:
        veh = data.get("GetVehAvailRS", {}).get("VehAvailInfos", {}).get("VehAvailInfo", [])
        if not veh:
            return self._fallback_car(airport, pick_up, drop_off)

        info = veh[0]
        vendor = info.get("Vendor", {}).get("Name", "Rental car")
        charges = info.get("VehAvailCore", {}).get("TotalCharge", {})
        total = normalize_sabre_price(float(charges.get("RateTotalAmount", 0) or 0), "car")
        if total <= 0:
            return self._fallback_car(airport, pick_up, drop_off)

        vehicle = info.get("VehAvailCore", {}).get("Vehicle", {})
        veh_type = vehicle.get("VehType", "Standard")
        days = max(1, (date.fromisoformat(drop_off) - date.fromisoformat(pick_up)).days)
        return {
            "price": round(total, 2),
            "currency": "USD",
            "title": f"{vendor} {veh_type}",
            "description": f"{days} day(s) · Airport pickup at {airport}",
            "details": {
                "vendor": vendor,
                "class": veh_type,
                "source": "sabre",
            },
        }

    @staticmethod
    def next_weekend() -> tuple[str, str]:
        today = date.today()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() != 4:
            days_until_friday = 7
        if today.weekday() >= 5:
            days_until_friday = (4 - today.weekday()) % 7 or 7
        friday = today + timedelta(days=days_until_friday)
        sunday = friday + timedelta(days=2)
        return friday.isoformat(), sunday.isoformat()
