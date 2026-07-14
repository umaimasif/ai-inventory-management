"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/app-shell";
import { ChartCard } from "@/components/charts";
import { EmptyState, money } from "@/components/ui";
import { analytics } from "@/lib/resources";
import type { DailyReport, TopCategory } from "@/lib/types";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function ReportsPage() {
  const [day, setDay] = useState(todayIso());
  const [report, setReport] = useState<DailyReport | null>(null);
  const [cats, setCats] = useState<TopCategory[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([analytics.dailyReport(day), analytics.topCategories(30)])
      .then(([r, c]) => {
        setReport(r);
        setCats(c);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, [day]);

  useEffect(load, [load]);

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Daily business summary"
        action={
          <input
            type="date"
            value={day}
            max={todayIso()}
            onChange={(e) => setDay(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          />
        }
      />

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: "Revenue", value: report && money(report.revenue) },
          { label: "Profit", value: report && money(report.profit) },
          { label: "Orders", value: report?.orders },
          { label: "Units sold", value: report?.units_sold },
        ].map((tile) => (
          <div
            key={tile.label}
            className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-950"
          >
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
              {tile.label}
            </p>
            <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">
              {loading ? "—" : (tile.value ?? 0)}
            </p>
          </div>
        ))}
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Best sellers" subtitle={`On ${day}`}>
          {loading ? (
            <EmptyState>Loading…</EmptyState>
          ) : !report || report.top_products.length === 0 ? (
            <EmptyState>No sales on this day.</EmptyState>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Units</th>
                  <th className="pb-2 font-medium">Revenue</th>
                  <th className="pb-2 font-medium">Profit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {report.top_products.map((p) => (
                  <tr key={p.product_id} className="text-gray-800 dark:text-gray-200">
                    <td className="py-2">{p.name}</td>
                    <td className="py-2 tabular-nums">{p.units_sold}</td>
                    <td className="py-2 tabular-nums">{money(p.revenue)}</td>
                    <td className="py-2 tabular-nums text-emerald-700 dark:text-emerald-400">
                      {money(p.profit)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ChartCard>

        {/* Table view of the category breakdown — the accessible counterpart
            to any colored chart, and readable without color at all. */}
        <ChartCard title="Top categories" subtitle="Last 30 days, by revenue">
          {loading ? (
            <EmptyState>Loading…</EmptyState>
          ) : cats.length === 0 ? (
            <EmptyState>No sales in this period.</EmptyState>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-gray-500 dark:text-gray-400">
                <tr>
                  <th className="pb-2 font-medium">Category</th>
                  <th className="pb-2 font-medium">Units</th>
                  <th className="pb-2 font-medium">Revenue</th>
                  <th className="pb-2 font-medium">Profit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {cats.map((c) => (
                  <tr
                    key={c.category_id ?? "none"}
                    className="text-gray-800 dark:text-gray-200"
                  >
                    <td className="py-2">{c.name}</td>
                    <td className="py-2 tabular-nums">{c.units_sold}</td>
                    <td className="py-2 tabular-nums">{money(c.revenue)}</td>
                    <td className="py-2 tabular-nums text-emerald-700 dark:text-emerald-400">
                      {money(c.profit)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </ChartCard>
      </section>

      <section className="mt-4 grid grid-cols-2 gap-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-950">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Low stock items
          </p>
          <p className="mt-2 text-3xl font-semibold text-amber-700 dark:text-amber-400">
            {loading ? "—" : (report?.low_stock_count ?? 0)}
          </p>
        </div>
        <div className="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-950">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            Out of stock
          </p>
          <p className="mt-2 text-3xl font-semibold text-red-700 dark:text-red-400">
            {loading ? "—" : (report?.out_of_stock_count ?? 0)}
          </p>
        </div>
      </section>
    </div>
  );
}
