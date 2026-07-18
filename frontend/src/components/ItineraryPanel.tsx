"use client";

import { formatMoney } from "@/lib/formatMoney";
import type { Itinerary } from "@/types/trip";

type Props = {
  itinerary: Itinerary | null;
  loading?: boolean;
  activeActivityId?: string | null;
  onHoverActivity?: (activityId: string | null) => void;
};

const PERIOD_STYLE: Record<string, { dot: string; label: string }> = {
  Morning: { dot: "bg-amber-400", label: "text-amber-300" },
  Afternoon: { dot: "bg-sky-400", label: "text-sky-300" },
  Evening: { dot: "bg-violet-400", label: "text-violet-300" },
};

export default function ItineraryPanel({
  itinerary,
  loading,
  activeActivityId,
  onHoverActivity,
}: Props) {
  if (loading) {
    return (
      <div className="px-5 py-4">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Itinerary</p>
        <p className="mt-2 text-xs text-zinc-500">Building your day-by-day plan...</p>
      </div>
    );
  }

  if (!itinerary || !itinerary.days.length) {
    return (
      <div className="px-5 py-4">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Itinerary</p>
        <p className="mt-2 text-xs text-zinc-500">
          Tap <span className="font-medium text-zinc-300">Plan day trip</span> on the map to generate
          a morning-to-evening plan for this destination.
        </p>
      </div>
    );
  }

  let counter = 0;

  return (
    <div className="px-4 py-4">
      <div className="mb-3 px-1">
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Itinerary</p>
        <h2 className="text-base font-semibold text-white">
          {itinerary.days.length}-day plan for {itinerary.destination_city}
        </h2>
      </div>

      <div className="space-y-4">
        {itinerary.days.map((day) => (
          <div key={day.day_index}>
            <p className="mb-1.5 px-1 text-xs font-semibold text-zinc-200">{day.title}</p>
            <ol className="space-y-1.5">
              {day.segments.map((segment) => {
                counter += 1;
                const marker = counter;
                const style = PERIOD_STYLE[segment.period] ?? PERIOD_STYLE.Morning;
                const active = activeActivityId === segment.activity.id;
                return (
                  <li
                    key={segment.activity.id}
                    onMouseEnter={() => onHoverActivity?.(segment.activity.id)}
                    onMouseLeave={() => onHoverActivity?.(null)}
                    className={`flex gap-3 rounded-xl border px-3 py-2 transition ${
                      active
                        ? "border-white/25 bg-zinc-900"
                        : "border-white/8 bg-zinc-950/70 hover:border-white/15"
                    }`}
                  >
                    <div className="flex flex-col items-center pt-0.5">
                      <span
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-bold text-black ${style.dot}`}
                      >
                        {marker}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-[10px] font-semibold uppercase tracking-wide ${style.label}`}>
                          {segment.period} · {segment.time_label}
                        </p>
                        {segment.activity.cost_estimate ? (
                          <span className="shrink-0 text-[10px] text-zinc-500">
                            ~{formatMoney(segment.activity.cost_estimate)}
                          </span>
                        ) : (
                          <span className="shrink-0 text-[10px] text-emerald-400">Free</span>
                        )}
                      </div>
                      <p className="truncate text-sm font-medium text-white">{segment.activity.name}</p>
                      <p className="mt-0.5 text-[11px] leading-relaxed text-zinc-500">
                        {segment.activity.description}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        ))}
      </div>
    </div>
  );
}
