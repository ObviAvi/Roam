const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function queryAgent(query: string, sessionId: string) {
  const response = await fetch(`${API_BASE}/api/agent/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!response.ok) {
    throw new Error("Agent query failed");
  }
  return response.json();
}

export async function selectTrip(sessionId: string, optionId: string) {
  const response = await fetch(`${API_BASE}/api/trips/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, option_id: optionId }),
  });
  if (!response.ok) {
    throw new Error("Trip selection failed");
  }
  return response.json();
}

export async function getItinerary(sessionId: string, optionId: string) {
  const response = await fetch(`${API_BASE}/api/trips/itinerary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, option_id: optionId }),
  });
  if (!response.ok) {
    throw new Error("Itinerary generation failed");
  }
  return response.json();
}
