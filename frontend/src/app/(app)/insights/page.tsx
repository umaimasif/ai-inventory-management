"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/app-shell";
import { ChartCard } from "@/components/charts";
import { EmptyState, money } from "@/components/ui";
import { insights } from "@/lib/resources";
import type {
  DeadStockItem,
  FrequentlyBoughtTogether,
  WorstSeller,
} from "@/lib/types";

const RANGES = [
  { days: 7, label: "7 days" },
  { days: 30, label: "30 days" },
  { days: 90, label: "90 days" },
];

export default function InsightsPage() {
  const [days, setDays] = useState(30);
  const [worst, setWorst] = useState<WorstSeller[]>([]);
  const [dead, setDead] = useState<DeadStockItem[]>([]);
  const [fbt, setFbt] = useState<FrequentlyBoughtTogether | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      insights.worstSellers(days, 8),
      insights.deadStock(days),
      insights.frequentlyBoughtTogether(days, 8),
    ])
      .then(([w, d, f]) => {
        setWorst(w);
        setDead(d);
        setFbt(f);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(load, [load]);

  return (
    <div>
      <PageHeader
        title="Insights"
        subtitle="Slow movers, dead stock, and buying patterns"
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

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Slow movers" subtitle="Fewest units sold in this period">
          {loading ? (
            <EmptyState>Loading…</EmptyState>
          ) : worst.length === 0 ? (
            <EmptyState>No products yet.</EmptyState>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Units sold</th>
                  <th className="pb-2 font-medium">In stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {worst.map((w) => (
                  <tr key={w.product_id} className="text-gray-800 dark:text-gray-200">
                    <td className="py-2">
                      {w.name}
                      <span className="ml-2 text-xs text-gray-400">{w.sku}</span>
                    </td>
                    <td className="py-2 tabular-nums">
                      {w.units_sold === 0 ? (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950/60 dark:text-red-300">
                          0 sold
                        </span>
                      ) : (
                        w.units_sold
                      )}
                    </td>
                    <td className="py-2 tabular-nums">{w.stock_quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ChartCard>

        <ChartCard
          title="Dead stock"
          subtitle="Holding stock with no recent sales — cash tied up"
        >
          {loading ? (
            <EmptyState>Loading…</EmptyState>
          ) : dead.length === 0 ? (
            <EmptyState>No dead stock. Everything is moving. 🎉</EmptyState>
          ) : (
            <ul className="space-y-3">
              {dead.map((d) => (
                <li
                  key={d.product_id}
                  className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {d.name}
                    </span>
                    <span className="text-sm font-medium text-amber-700 dark:text-amber-400">
                      {money(d.capital_tied_up)} tied up
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {d.reason}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>
      </div>

      <div className="mt-4">
        <ChartCard
          title="Frequently bought together"
          subtitle="Products that show up in the same sale — bundle candidates"
        >
          {loading ? (
            <EmptyState>Loading…</EmptyState>
          ) : !fbt?.enough_data ? (
            <EmptyState>
              Not enough sales yet to find reliable patterns (
              {fbt?.total_sales ?? 0} of {fbt?.min_sales_required ?? 20} needed).
              This unlocks automatically as more sales are recorded.
            </EmptyState>
          ) : fbt.pairs.length === 0 ? (
            <EmptyState>No pairs found — sales rarely combine products.</EmptyState>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="pb-2 font-medium">Pair</th>
                  <th className="pb-2 font-medium">Bought together</th>
                  <th className="pb-2 font-medium">Support</th>
                  <th className="pb-2 font-medium">Suggestion</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {fbt.pairs.map((p) => (
                  <tr
                    key={`${p.product_a_id}-${p.product_b_id}`}
                    className="text-gray-800 dark:text-gray-200"
                  >
                    <td className="py-2">
                      {p.product_a_name} + {p.product_b_name}
                    </td>
                    <td className="py-2 tabular-nums">{p.together_count}×</td>
                    <td className="py-2 tabular-nums">
                      {Math.round(p.support * 100)}%
                    </td>
                    <td className="py-2 text-gray-500 dark:text-gray-400">
                      Bundle or place near each other
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ChartCard>
      </div>
    </div>
  );
}
