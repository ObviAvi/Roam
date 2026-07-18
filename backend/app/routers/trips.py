from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    RecommendationsResponse,
    SelectTripRequest,
    TripPlanResponse,
    TripRequest,
    UserPreferences,
)
from app.services.agent import handle_agent_query
from app.services.memory import (
    get_selected_option,
    get_session_options,
    load_preferences,
    save_selected_option,
)
from app.services.planner import build_recommendations, build_trip_plan, parse_user_message

router = APIRouter(prefix="/api", tags=["trips"])


@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripRequest) -> TripPlanResponse:
    merged = parse_user_message("", request.session_id)
    if request.origin:
        merged.origin = request.origin
    if request.budget:
        merged.budget = request.budget
    if request.travelers:
        merged.travelers = request.travelers
    if request.trip_style:
        merged.trip_style = request.trip_style
    return await build_trip_plan(merged)


@router.get("/trips/{session_id}")
async def get_trips(session_id: str) -> dict:
    return {"options": get_session_options(session_id)}


@router.post("/trips/select")
async def select_trip(payload: SelectTripRequest) -> dict:
    options = get_session_options(payload.session_id)
    selected = next((o for o in options if o.get("id") == payload.option_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Trip option not found")
    save_selected_option(payload.session_id, payload.option_id)
    recs = build_recommendations(selected)
    return {"option": selected, "recommendations": recs}


@router.get("/trips/{session_id}/selected")
async def get_selected(session_id: str) -> dict:
    option = get_selected_option(session_id)
    if not option:
        raise HTTPException(status_code=404, detail="No trip selected")
    return {"option": option, "recommendations": build_recommendations(option)}


@router.get("/trips/{session_id}/recommendations", response_model=RecommendationsResponse)
async def recommendations(session_id: str) -> RecommendationsResponse:
    option = get_selected_option(session_id)
    if not option:
        raise HTTPException(status_code=404, detail="No trip selected")
    return build_recommendations(option)
