from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import TripRequest, UserPreferences

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MEMORY_FILE = DATA_DIR / "memory.json"
SESSIONS_DIR = DATA_DIR / "sessions"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def load_preferences(user_id: str = "default") -> UserPreferences:
    _ensure_dirs()
    if not MEMORY_FILE.exists():
        return UserPreferences()

    data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    user = data.get("users", {}).get(user_id, {})
    return UserPreferences(**user)


def save_preferences(prefs: UserPreferences, user_id: str = "default") -> None:
    _ensure_dirs()
    data = {"users": {}}
    if MEMORY_FILE.exists():
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    data.setdefault("users", {})[user_id] = prefs.model_dump()
    MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def merge_trip_request(session_id: str, updates: TripRequest) -> TripRequest:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    existing: dict = {}
    if session_file.exists():
        existing = json.loads(session_file.read_text(encoding="utf-8"))

    merged = {**existing, **updates.model_dump(exclude_none=True)}
    prefs = load_preferences(session_id)
    if updates.preferences.notes or updates.preferences.trip_styles:
        prefs.activity_interests = list(
            set(prefs.activity_interests + updates.preferences.activity_interests)
        )
        prefs.trip_styles = list(set(prefs.trip_styles + updates.preferences.trip_styles))
        prefs.notes = list(set(prefs.notes + updates.preferences.notes))
        if updates.preferences.preferred_flight_times:
            prefs.preferred_flight_times = updates.preferences.preferred_flight_times
        if updates.preferences.hotel_style:
            prefs.hotel_style = updates.preferences.hotel_style
        if updates.travelers:
            prefs.default_travelers = updates.travelers
        save_preferences(prefs, session_id)
        merged["preferences"] = prefs.model_dump()

    session_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return TripRequest(**merged)


def get_session_request(session_id: str) -> TripRequest:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    prefs = load_preferences(session_id)
    if not session_file.exists():
        return TripRequest(session_id=session_id, preferences=prefs)
    data = json.loads(session_file.read_text(encoding="utf-8"))
    data.setdefault("preferences", prefs.model_dump())
    data["session_id"] = session_id
    return TripRequest(**data)


def save_session_options(session_id: str, options: list[dict]) -> None:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    data = {}
    if session_file.exists():
        data = json.loads(session_file.read_text(encoding="utf-8"))
    data["last_options"] = options
    session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_session_options(session_id: str) -> list[dict]:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return []
    data = json.loads(session_file.read_text(encoding="utf-8"))
    return data.get("last_options", [])


def save_selected_option(session_id: str, option_id: str) -> None:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    data = {}
    if session_file.exists():
        data = json.loads(session_file.read_text(encoding="utf-8"))
    data["selected_option_id"] = option_id
    session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_selected_option(session_id: str) -> dict | None:
    _ensure_dirs()
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return None
    data = json.loads(session_file.read_text(encoding="utf-8"))
    option_id = data.get("selected_option_id")
    if not option_id:
        return None
    for option in data.get("last_options", []):
        if option.get("id") == option_id:
            return option
    return None
