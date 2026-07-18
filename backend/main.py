import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import agent, trips, voice

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Roam Trip Planner API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice.router)
app.include_router(trips.router)
app.include_router(agent.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
