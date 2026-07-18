from fastapi import APIRouter

from app.models.schemas import AgentQueryRequest, AgentQueryResponse, UserPreferences
from app.services.agent import handle_agent_query
from app.services.memory import load_preferences, save_preferences

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/agent/query", response_model=AgentQueryResponse)
async def agent_query(payload: AgentQueryRequest) -> AgentQueryResponse:
    return await handle_agent_query(payload)


@router.get("/memory/{user_id}", response_model=UserPreferences)
async def get_memory(user_id: str = "default") -> UserPreferences:
    return load_preferences(user_id)


@router.put("/memory/{user_id}", response_model=UserPreferences)
async def update_memory(user_id: str, prefs: UserPreferences) -> UserPreferences:
    save_preferences(prefs, user_id)
    return prefs
