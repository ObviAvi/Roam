type Props = {
  compact?: boolean;
};

export default function TripSearchIndicator({ compact = false }: Props) {
  return (
    <div
      className={`flex items-center gap-3 rounded-2xl border border-sky-400/20 bg-sky-500/10 ${
        compact ? "px-3 py-2.5" : "px-4 py-3"
      }`}
    >
      <div
        className={`animate-spin rounded-full border-2 border-sky-300/25 border-t-sky-200 ${
          compact ? "h-4 w-4 shrink-0" : "h-5 w-5 shrink-0"
        }`}
        aria-hidden="true"
      />
      <div>
        <p className={`font-medium text-sky-100 ${compact ? "text-xs" : "text-sm"}`}>
          Searching for trips
        </p>
        <p className={`text-sky-200/70 ${compact ? "text-[11px]" : "text-xs"}`}>
          Checking Sabre for flights, hotels, and rental cars…
        </p>
      </div>
    </div>
  );
}
