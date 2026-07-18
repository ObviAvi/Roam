# Roam — AI Trip Planner

Voice-enabled weekend trip planner built for the Sabre × Vocal Bridge hackathon. Talk to **Roam**, your travel concierge, and get complete trip options with real Sabre flight, hotel, and rental car inventory, weather-aware recommendations, and a Mapbox trip visualization.

## Features

- **Conversational planning** via Vocal Bridge voice agent
- **Sabre inventory search** for flights, hotels, and rental cars
- **Exact listings & prices** shown in the UI for each option
- **Weather-aware guidance** via Open-Meteo
- **Personalized memory** stored between sessions (`backend/data/memory.json`)
- **Mapbox map** zooms into your selected destination
- **Gemini day planner** builds a morning-to-evening itinerary (web-search grounded), mapped with pins and arrows
- **Recommendations** for packing, tips, and weather notes

## Project structure

```
backend/          FastAPI API (Sabre, planner, memory, voice token proxy)
frontend/         Next.js app with globe, voice UI, trip cards, map
vocal-bridge/     Agent prompt + client actions + AI agent config
scripts/          Setup helpers
```

## Quick start

### 1. Environment

Copy your keys into `.env` at the repo root (you already have one). Required keys:

- `VOCAL_BRIDGE_API_KEY` (or `VOCAL_BRIDE_API_KEY`)
- `SABRE_API_KEY`
- `MAPBOX_TOKEN`

Optional:

- `VOCAL_BRIDGE_AGENT_ID` — required if using an account-level Vocal Bridge key
- `GEMINI_API_KEY` — enables the "Plan day trip" itinerary generator (Google AI Studio)

Sync frontend env:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/sync_frontend_env.ps1
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Vocal Bridge agent

Install the CLI and configure your agent:

```powershell
pip install vocal-bridge
python scripts/setup_vocal_bridge.py
```

This creates a **Trip Planner** agent (if needed), sets the system prompt, enables AI Agent mode, and registers client actions.

If you use an account-level API key, run `vb agent list`, copy the agent UUID, and add it to `.env`:

```
VOCAL_BRIDGE_AGENT_ID=your-agent-uuid
```

## How it works

1. The **Vocal Bridge voice agent** handles the conversation and delegates domain questions to your backend via **AI Agent mode**.
2. The **Next.js frontend** receives `aiAgentQuery` events and calls `POST /api/agent/query`.
3. The **FastAPI backend** parses trip intent, searches **Sabre** for flights/hotels/cars across multiple destinations, adds **weather** context, and returns structured trip options.
4. The UI renders exact listings and prices. When you select a trip, **Mapbox** flies to the destination and recommendations appear.

## API endpoints

| Endpoint | Description |
|---|---|
| `POST /api/voice-token` | Proxy Vocal Bridge token (keeps API key server-side) |
| `POST /api/agent/query` | AI Agent backend for voice delegation |
| `POST /api/plan` | Direct trip planning |
| `GET /api/trips/{session_id}` | Cached trip options |
| `POST /api/trips/select` | Select a trip + get recommendations |
| `POST /api/trips/itinerary` | Gemini day-by-day plan for a selected trip |
| `GET /api/memory/{user_id}` | User preference memory |

## Voice demo script

> "I'm leaving from Los Angeles with a $500 budget for a food-focused weekend for 2 people."

Then:

> "Show me the options" or "Search for trips"

Select a trip in the UI or say:

> "I'll take option 1"

## Sabre notes

The backend uses Sabre REST endpoints on the certification platform:

- `POST /v5/offers/shop` — flights
- `POST /v4.1.0/hotel/avail` — hotels
- `POST /v2.0/veh/avail` — rental cars

If a Sabre call fails (sandbox limits, PCC, etc.), the planner falls back to realistic estimates so the demo still works end-to-end. See the [Sabre Developer Hub](https://developer.sabre.com/product-collection/hackathon-2026/v1/index.html) for hackathon-specific docs.

## Troubleshooting

- **403 on voice token**: Verify your Vocal Bridge API key and agent ID.
- **No microphone**: Allow browser mic permissions; voice connect must be triggered by a click.
- **Empty map**: Run `scripts/sync_frontend_env.ps1` so `NEXT_PUBLIC_MAPBOX_TOKEN` is set.
- **Sabre errors in logs**: Check `SABRE_API_KEY` expiry and `SABRE_BASE_URL`.
