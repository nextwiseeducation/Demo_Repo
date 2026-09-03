interface StatTileProps {
  label: string;
  value: string | number | null;
  /** Rendered after the value, e.g. "%" — kept separate so null-value formatting doesn't have to special-case it. */
  suffix?: string;
}

/** value=null renders an em-dash: used for metrics with no meaningful baseline yet (e.g. MoM growth on day one). */
export function StatTile({ label, value, suffix }: StatTileProps) {
  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-border bg-card px-4 py-3">
      <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</span>
      <span className="font-display text-lg font-semibold text-foreground">
        {value === null ? "—" : `${value}${suffix ?? ""}`}
      </span>
    </div>
  );
}
