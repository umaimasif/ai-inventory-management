"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/app-shell";
import { ChartCard } from "@/components/charts";
import { ConfidenceBadge, EmptyState } from "@/components/ui";
import { insights } from "@/lib/resources";
import type { ProductForecast } from "@/lib/types";

const RANGES = [
  { days: 30, label: "30 days" },
  { days: 60, label: "60 days" },
  { days: 90, label: "90 days" },
];

function DaysLeftCell({ days }: { days: number | null }) {
  if (days === null) {
    return <span className="text-gray-400">no demand</span>;
  }
  const tone =
    days <= 3
      ? "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300"
      : days <= 10
        ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
        : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium tabular-nums ${tone}`}>
      {days} days
    </span>
  );
}

export default function ForecastPage() {
  const [days, setDays] = useState(30);
  const [rows, setRows] = useState<ProductForecast[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    insights
      .forecast(days)
      .then(setRows)
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(load, [load]);

  const needsReorder = rows.filter((r) => r.recommended_reorder_qty > 0);

  return (
    <div>
      <PageHeader
        title="Forecast"
        subtitle="Demand estimate and reorder guidance"
        action={
          <div className="flex gap-1 rounded-lg border border-gray-200 p-1 dark:border-gray-800">
            {RANGES.map((r) => (
              <button
                key={r.days}
                onClick={() => setDays(r.days)}
                className={`rounded-md px-3 py-1 text-sm font-medium transition ${
                  days === r.days
                    ? "bg-indigo-600 text-white"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        }
      />

      <div className="mb-4 rounded-xl border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-900 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-200">
        <strong>{needsReorder.length}</strong> product
        {needsReorder.length === 1 ? "" : "s"} need reordering. Estimates use a
        moving average over the selected window — not a trained model — so each
        row shows its confidence.
      </div>

      <ChartCard title="Reorder plan" subtitle="Sorted by soonest to run out">
        {loading ? (
          <EmptyState>Loading…</EmptyState>
        ) : rows.length === 0 ? (
          <EmptyState>No products yet.</EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">In stock</th>
                  <th className="pb-2 font-medium">Avg/day</th>
                  <th className="pb-2 font-medium">Stock left</th>
                  <th className="pb-2 font-medium">Reorder</th>
                  <th className="pb-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {rows.map((r) => (
                  <tr
                    key={r.product_id}
                    className="align-top text-gray-800 dark:text-gray-200"
                  >
                    <td className="py-2">
                      <div className="font-medium">{r.name}</div>
                      <div className="mt-0.5 max-w-md text-xs text-gray-500 dark:text-gray-400">
                        {r.reason}
                      </div>
                    </td>
                    <td className="py-2 tabular-nums">{r.stock_quantity}</td>
                    <td className="py-2 tabular-nums">{r.avg_daily_demand}</td>
                    <td className="py-2">
                      <DaysLeftCell days={r.days_of_stock_left} />
                    </td>
                    <td className="py-2">
                      {r.recommended_reorder_qty > 0 ? (
                        <span className="font-semibold text-indigo-700 tabular-nums dark:text-indigo-300">
                          +{r.recommended_reorder_qty}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="py-2">
                      <ConfidenceBadge level={r.confidence} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ChartCard>
    </div>
  );
}
