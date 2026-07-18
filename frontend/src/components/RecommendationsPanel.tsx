"use client";

import type { Recommendations } from "@/types/trip";

type Props = {
  recommendations: Recommendations;
};

export default function RecommendationsPanel({ recommendations }: Props) {
  return (
    <section className="border-t border-white/8 px-5 py-4">
      <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-500">Recommendations</p>
      <h2 className="text-sm font-semibold text-white">For {recommendations.destination}</h2>

      <div className="mt-3 space-y-3">
        <div>
          <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Bring</h3>
          <ul className="space-y-1 text-xs text-zinc-300">
            {recommendations.packing.slice(0, 4).map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500">Keep in mind</h3>
          <ul className="space-y-1 text-xs text-zinc-300">
            {[...recommendations.tips.slice(0, 2), ...recommendations.weather_notes.slice(0, 1)].map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
