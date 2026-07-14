"use client";

// Stat tile: a headline value with its change vs the previous period.
// A single current value is a stat tile, not a one-bar bar chart.

import type { KpiValue } from "@/lib/types";

function DeltaBadge({ changePct }: { changePct: number | null }) {
  // Undefined change (no baseline) is stated, not faked as 0%.
  if (changePct === null) {
    return <span className="text-xs text-gray-400">no prior data</span>;
  }

  const up = changePct >= 0;
  const cls = up
    ? "text-emerald-700 dark:text-emerald-400"
    : "text-red-700 dark:text-red-400";

  return (
    <span className={`text-xs font-medium ${cls}`}>
      {/* Arrow + sign, so direction is never carried by color alone. */}
      {up ? "▲" : "▼"} {up ? "+" : ""}
      {changePct}%
    </span>
  );
}

export function StatTile({
  label,
  kpi,
  format = (n) => String(n),
}: {
  label: string;
  kpi: KpiValue | undefined;
  format?: (value: number) => string;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-950">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
        {label}
      </p>
      <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">
        {kpi ? format(kpi.current) : "—"}
      </p>
      <div className="mt-1">
        {kpi ? <DeltaBadge changePct={kpi.change_pct} /> : null}
      </div>
    </div>
  );
}

/** Plain count tile with no comparison (inventory state, not a trend). */
export function CountTile({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number | undefined;
  tone?: "neutral" | "warning" | "critical";
}) {
  const toneCls =
    tone === "critical"
      ? "text-red-700 dark:text-red-400"
      : tone === "warning"
        ? "text-amber-700 dark:text-amber-400"
        : "text-gray-900 dark:text-white";

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-950">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
        {label}
      </p>
      <p className={`mt-2 text-3xl font-semibold ${toneCls}`}>{value ?? "—"}</p>
    </div>
  );
}
