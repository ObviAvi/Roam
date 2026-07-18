"use client";

import GlobeBackground from "@/components/GlobeBackground";

type Props = {
  onEnter: () => void;
};

export default function LandingHero({ onEnter }: Props) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onEnter}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onEnter();
        }
      }}
      className="group relative h-screen w-screen cursor-pointer overflow-hidden bg-black text-white"
    >
      <div className="absolute inset-0 opacity-70">
        <GlobeBackground rotateSpeed={0.14} fillContainer />
      </div>

      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_20%,rgba(0,0,0,0.75)_100%)]" />

      <div className="relative flex h-full flex-col items-center justify-center px-6 text-center">
        <p className="mb-4 text-[11px] font-medium uppercase tracking-[0.4em] text-zinc-400">
          Vocal Bridge × Sabre
        </p>

        <h1 className="bg-gradient-to-r from-white via-zinc-100 to-zinc-400 bg-clip-text text-6xl font-semibold tracking-[0.3em] text-transparent md:text-8xl">
          ROAM
        </h1>

        <p className="mt-5 max-w-xl text-base leading-relaxed text-zinc-300 md:text-lg">
          Your  weekend trip concierge. Just tell Roam your budget, vibe, and who&apos;s
          coming. It finds real flights, hotels, and rental cars, then maps a day-by-day plan for
          your getaway.
        </p>

        <div className="mt-9 inline-flex items-center gap-2 rounded-full bg-white px-7 py-3 text-sm font-semibold text-black transition group-hover:scale-[1.03] group-hover:bg-zinc-100">
          Start planning
          <span className="transition group-hover:translate-x-0.5">→</span>
        </div>

        <p className="absolute bottom-8 text-[11px] tracking-[0.2em] text-zinc-600">
          Click anywhere to begin
        </p>
      </div>
    </div>
  );
}
