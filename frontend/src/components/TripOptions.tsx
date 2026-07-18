"use client";

import { useState } from "react";
import { formatMoney } from "@/lib/formatMoney";
import type { TripOption } from "@/types/trip";

type Props = {
  options: TripOption[];
  selectedId?: string | null;
  onSelect: (option: TripOption) => void;
};

const CITY_EMOJI: Record<string, string> = {
  Austin: "🎸",
  Denver: "🏔️",
  Nashville: "🎶",
  "San Diego": "🌊",
  Portland: "☕",
  Miami: "🌴",
};

export default function TripOptions({ options, selectedId, onSelect }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!options.length) {
    return (
      <div className="px-5 py-8 text-center">
        <p className="text-sm font-medium text-zinc-300">No trips yet</p>
        <p className="mt-1 text-xs text-zinc-500">
          Start a voice session and tell Roam your origin, budget, and travel style.
        </p>
      </div>
    );
  }

  return (
    <div className="px-3 py-3">
      <div className="mb-3 px-2">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Results</p>
        <h2 className="text-base font-semibold text-white">{options.length} weekend options</h2>
      </div>

      <div className="space-y-2">
        {options.map((option, index) => {
          const expanded = expandedId === option.id;
          const selected = selectedId === option.id;
          const emoji = CITY_EMOJI[option.destination_city] || "✈️";

          return (
            <article
              key={option.id}
              className={`rounded-2xl border transition ${
                selected
                  ? "border-white/20 bg-zinc-900"
                  : "border-white/8 bg-zinc-950/80 hover:border-white/15"
              }`}
            >
              <button
                type="button"
                onClick={() => setExpandedId(expanded ? null : option.id)}
                className="flex w-full items-center gap-3 px-3 py-3 text-left"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-lg">
                  {emoji}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-semibold text-white">
                      {option.destination_city}
                      {option.destination_state ? `, ${option.destination_state}` : ""}
                    </p>
                    <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400">
                      Option {index + 1}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-emerald-400">
                    Flights {formatMoney(option.flight_price)} · Hotel {formatMoney(option.hotel_price)} · Car{" "}
                    {formatMoney(option.car_price)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-white">{formatMoney(option.total_price)}</p>
                  {option.within_budget === false ? (
                    <p className="text-[10px] font-medium text-amber-400">
                      +{formatMoney(option.over_budget_by ?? 0)} over
                    </p>
                  ) : (
                    <p className="text-[10px] text-zinc-500">total</p>
                  )}
                </div>
              </button>

              {expanded ? (
                <div className="space-y-2 border-t border-white/8 px-3 pb-3 pt-2">
                  {option.listings.map((listing) => (
                    <div
                      key={`${option.id}-${listing.category}`}
                      className="rounded-xl bg-black/25 px-3 py-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-medium text-zinc-200">
                          {listing.category === "flight" && "✈ "}
                          {listing.category === "hotel" && "🏨 "}
                          {listing.category === "car" && "🚗 "}
                          {listing.title}
                        </p>
                        <p className="shrink-0 text-xs font-medium text-zinc-100">
                          {formatMoney(listing.price)}
                        </p>
                      </div>
                      <p className="mt-1 text-[11px] text-zinc-500">{listing.description}</p>
                    </div>
                  ))}

                  {option.weather?.summary ? (
                    <p className="rounded-xl bg-amber-500/10 px-3 py-2 text-[11px] leading-relaxed text-amber-100">
                      {option.weather.summary}
                    </p>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => onSelect(option)}
                    className="w-full rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black hover:bg-zinc-200"
                  >
                    Select this trip
                  </button>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </div>
  );
}
