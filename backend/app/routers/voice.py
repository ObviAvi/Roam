import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(prefix="/api", tags=["voice"])


class VoiceTokenRequest(BaseModel):
    participant_name: str = "Roam User"
    session_id: str | None = None


@router.post("/voice-token")
async def voice_token(body: VoiceTokenRequest) -> dict:
    settings = get_settings()
    if not settings.vocal_bridge_api_key:
        raise HTTPException(status_code=500, detail="VOCAL_BRIDGE_API_KEY is not configured")

    headers = {
        "X-API-Key": settings.vocal_bridge_api_key,
        "Content-Type": "application/json",
    }
    if settings.vocal_bridge_agent_id:
        headers["X-Agent-Id"] = settings.vocal_bridge_agent_id

    payload = {"participant_name": body.participant_name}
    if body.session_id:
        payload["session_id"] = body.session_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.vocal_bridge_url}/api/v1/token",
            headers=headers,
            json=payload,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get("/agent-info")
async def agent_info() -> dict:
    settings = get_settings()
    if not settings.vocal_bridge_api_key:
        raise HTTPException(status_code=500, detail="VOCAL_BRIDGE_API_KEY is not configured")

    headers = {"X-API-Key": settings.vocal_bridge_api_key}
    if settings.vocal_bridge_agent_id:
        headers["X-Agent-Id"] = settings.vocal_bridge_agent_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{settings.vocal_bridge_url}/api/v1/agent",
            headers=headers,
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
