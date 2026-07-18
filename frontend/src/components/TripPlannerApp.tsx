"use client";

import { useMemo, useState } from "react";
import GlobeBackground from "@/components/GlobeBackground";
import ItineraryPanel from "@/components/ItineraryPanel";
import LandingHero from "@/components/LandingHero";
import RecommendationsPanel from "@/components/RecommendationsPanel";
import RoamLogo from "@/components/RoamLogo";
import TripMap from "@/components/TripMap";
import TripSearchIndicator from "@/components/TripSearchIndicator";
import TripOptions from "@/components/TripOptions";
import VoicePanel from "@/components/VoicePanel";
import { getItinerary, selectTrip } from "@/lib/api";
import type { Itinerary, Recommendations, TripOption } from "@/types/trip";

export default function TripPlannerApp() {
  const sessionId = useMemo(() => crypto.randomUUID(), []);
  const [options, setOptions] = useState<TripOption[]>([]);
  const [selectedTrip, setSelectedTrip] = useState<TripOption | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendations | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [itineraryLoading, setItineraryLoading] = useState(false);
  const [itineraryError, setItineraryError] = useState<string | null>(null);
  const [activeActivityId, setActiveActivityId] = useState<string | null>(null);
  const [isConversing, setIsConversing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [entered, setEntered] = useState(false);
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "";

  const handleTripOptions = (nextOptions: TripOption[]) => {
    setOptions(nextOptions);
  };

  const handleTripSelected = async (option: TripOption, recs?: Recommendations) => {
    setSelectedTrip(option);
    setItinerary(null);
    setItineraryError(null);
    setActiveActivityId(null);
    if (recs) {
      setRecommendations(recs);
    } else {
      const result = await selectTrip(sessionId, option.id);
      setRecommendations(result.recommendations);
    }
  };

  const handlePlanDayTrip = async () => {
    if (!selectedTrip) return;
    setItineraryLoading(true);
    setItineraryError(null);
    try {
      const result = await getItinerary(sessionId, selectedTrip.id);
      setItinerary(result);
    } catch {
      setItinerary(null);
      setItineraryError("Couldn't generate a day plan. Check your Gemini key and try again.");
    } finally {
      setItineraryLoading(false);
    }
  };

  if (!entered) {
    return <LandingHero onEnter={() => setEntered(true)} />;
  }

  return (
    <div className="relative h-screen overflow-hidden bg-black p-3 text-white">
      <div className="pointer-events-none absolute right-6 top-6 z-30">
        <RoamLogo />
      </div>

      <div className="flex h-full overflow-hidden rounded-[28px] border border-white/10 bg-[#111114] shadow-2xl shadow-black/50">
        <aside className="flex w-[420px] shrink-0 flex-col border-r border-white/8 bg-[#141417]">
          <VoicePanel
            sessionId={sessionId}
            onTripOptions={handleTripOptions}
            onTripSelected={handleTripSelected}
            onConnectionChange={setIsConversing}
            onSearchingChange={setIsSearching}
          />

          <div className="flex-1 overflow-y-auto">
            <TripOptions
              options={options}
              selectedId={selectedTrip?.id}
              onSelect={(option) => handleTripSelected(option)}
            />

            {recommendations ? <RecommendationsPanel recommendations={recommendations} /> : null}
          </div>
        </aside>

        <main className="relative min-w-0 flex-1 overflow-hidden bg-[#0b0b0c]">
          {selectedTrip && mapboxToken ? (
            <>
              <TripMap
                trip={selectedTrip}
                mapboxToken={mapboxToken}
                itinerary={itinerary}
                activeActivityId={activeActivityId}
              />
              <div className="absolute inset-y-5 left-5 flex w-80 flex-col gap-3">
                <div className="shrink-0 rounded-2xl border border-white/10 bg-black/55 px-4 py-3 backdrop-blur">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-400">Selected trip</p>
                  <p className="text-lg font-semibold text-white">
                    {selectedTrip.destination_city}
                    {selectedTrip.destination_state ? `, ${selectedTrip.destination_state}` : ""}
                  </p>
                  <p className="text-xs text-zinc-400">
                    {selectedTrip.origin_airport} → {selectedTrip.destination_airport}
                  </p>
                  <button
                    type="button"
                    onClick={() => void handlePlanDayTrip()}
                    disabled={itineraryLoading}
                    className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:opacity-60"
                  >
                    {itineraryLoading ? (
                      <>
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-black/30 border-t-black" />
                        Planning your day...
                      </>
                    ) : itinerary ? (
                      "Regenerate day plan"
                    ) : (
                      "Plan day trip"
                    )}
                  </button>
                  {!itinerary && !itineraryLoading && !itineraryError ? (
                    <p className="mt-1.5 text-[11px] text-zinc-400">
                      Build a morning-to-evening plan, mapped with pins and arrows.
                    </p>
                  ) : null}
                  {itineraryError ? (
                    <p className="mt-1.5 text-[11px] text-amber-300">{itineraryError}</p>
                  ) : null}
                </div>

                {itineraryLoading || itinerary ? (
                  <div className="min-h-0 flex-1 overflow-y-auto rounded-2xl border border-white/10 bg-black/55 backdrop-blur">
                    <ItineraryPanel
                      itinerary={itinerary}
                      loading={itineraryLoading}
                      activeActivityId={activeActivityId}
                      onHoverActivity={setActiveActivityId}
                    />
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <div className="flex h-full items-center justify-center px-8">
              <div className="absolute inset-0">
                <GlobeBackground
                  rotateSpeed={0.08}
                  fillContainer
                  focus={
                    options[0]
                      ? { lat: options[0].destination_lat, lng: options[0].destination_lng }
                      : null
                  }
                />
              </div>
              <div className="relative max-w-md space-y-4">
                {isSearching ? <TripSearchIndicator /> : null}
                <div className="rounded-2xl border border-white/10 bg-black/45 px-5 py-4 text-center backdrop-blur">
                  <p className="text-sm font-medium text-white">
                    {selectedTrip
                      ? "Your map is loading"
                      : isSearching
                        ? "Roam is building your weekend options"
                        : isConversing
                          ? options.length
                            ? "Pick a trip from the list to see it on the map"
                            : "Tell Roam where you're flying from and your budget"
                          : options.length
                            ? "Select a trip on the left to zoom into your destination"
                            : "Start a voice session to discover weekend getaways"}
                  </p>
                  {!isSearching ? (
                    <p className="mt-1 text-xs text-zinc-400">
                      Real flights, hotels, and rental cars with exact prices
                    </p>
                  ) : null}
                </div>
              </div>
            </div>
          )}

          {selectedTrip && !mapboxToken ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[#0b0b0c] p-6 text-sm text-amber-200">
              Add NEXT_PUBLIC_MAPBOX_TOKEN to enable the trip map.
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}
