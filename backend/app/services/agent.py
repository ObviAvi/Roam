from __future__ import annotations

import json
import re

from app.config import get_settings
from app.models.schemas import AgentQueryRequest, AgentQueryResponse
from app.services.memory import get_selected_option, get_session_options, save_selected_option
from app.services.planner import (
    build_recommendations,
    build_trip_plan,
    missing_fields,
    parse_user_message,
)


PLAN_KEYWORDS = re.compile(
    r"\b(plan|search|find|book|options|itinerary|trips?|weekend|generate|show me|look for)\b",
    re.I,
)
SELECT_KEYWORDS = re.compile(r"\b(select|choose|pick|option\s+\d+|go with|want option)\b", re.I)


async def _maybe_openai_response(query: str, context: str) -> str | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise travel planning assistant. Use the provided structured context. "
                        "Keep responses short and conversational for voice."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nUser:\n{query}"},
            ],
            max_tokens=250,
        )
        return completion.choices[0].message.content
    except Exception:
        return None


async def handle_agent_query(payload: AgentQueryRequest) -> AgentQueryResponse:
    session_id = payload.session_id
    query = payload.query.strip()
    request = parse_user_message(query, session_id)

    if SELECT_KEYWORDS.search(query):
        options = get_session_options(session_id)
        if not options:
            return AgentQueryResponse(
                response="I don't have trip options yet. Tell me your origin, budget, and travel style and I'll search for trips.",
            )

        option_index = 0
        match = re.search(r"option\s+(\d+)", query, re.I)
        if match:
            option_index = max(0, int(match.group(1)) - 1)
        elif "second" in query.lower():
            option_index = 1
        elif "third" in query.lower():
            option_index = 2

        option_index = min(option_index, len(options) - 1)
        selected = options[option_index]
        save_selected_option(session_id, selected["id"])
        recs = build_recommendations(selected)
        response = (
            f"Great choice! {selected['destination_city']} looks perfect. "
            f"Your total is ${selected['total_price']:.0f}. "
            f"I've loaded the map and recommendations on your screen."
        )
        return AgentQueryResponse(
            response=response,
            action="select_trip",
            payload={
                "option": selected,
                "recommendations": recs.model_dump(),
            },
        )

    if PLAN_KEYWORDS.search(query):
        missing = missing_fields(request)
        if missing:
            return AgentQueryResponse(
                response=(
                    f"I'd love to plan your trip. I still need your {' and '.join(missing)}. "
                    "For example: 'I'm leaving from Seattle with a $600 budget for a food-focused weekend for 2 people.'"
                ),
            )

        plan = await build_trip_plan(request)
        llm = await _maybe_openai_response(query, json.dumps(plan.model_dump(), default=str))
        response = llm or plan.message
        return AgentQueryResponse(
            response=response,
            action="show_trip_options",
            payload={"options": [o.model_dump() for o in plan.options], "message": plan.message},
        )

    missing = missing_fields(request)
    if missing:
        return AgentQueryResponse(
            response=(
                "I'm your AI travel agent. Tell me where you're flying from, your budget, how many travelers, "
                "and what kind of weekend you want — adventure, food, beach, or nightlife — and I'll build complete trip options."
            ),
        )

    plan = await build_trip_plan(request)
    return AgentQueryResponse(
        response=plan.message,
        action="show_trip_options" if plan.options else None,
        payload={"options": [o.model_dump() for o in plan.options]} if plan.options else None,
    )
