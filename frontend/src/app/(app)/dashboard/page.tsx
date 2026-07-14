"use client";

import { useCallback, useEffect, useState } from "react";

import { PageHeader } from "@/components/app-shell";
import {
  ChartCard,
  PaymentMixBar,
  RevenueProfitChart,
  TopProductsChart,
} from "@/components/charts";
import { CountTile, StatTile } from "@/components/stat-tile";
import { EmptyState, money } from "@/components/ui";
import { analytics, inventory } from "@/lib/resources";
import type {
  AnalyticsKpis,
  DailyPoint,
  DashboardSummary,
  LowStockItem,
  PaymentSlice,
  TopProduct,
} from "@/lib/types";

// Preset ranges, per the filter spec: one row of presets above the charts.
const RANGES = [
  { days: 7, label: "7 days" },
  { days: 30, label: "30 days" },
  { days: 90, label: "90 days" },
];

export default function DashboardPage() {
  const [days, setDays] = useState(30);
  const [kpis, setKpis] = useState<AnalyticsKpis | null>(null);
  const [series, setSeries] = useState<DailyPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [payments, setPayments] = useState<PaymentSlice[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [lowStock, setLowStock] = useState<LowStockItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      analytics.kpis(days),
      analytics.daily(days),
      analytics.topProducts(days),
      analytics.paymentMix(days),
      inventory.summary(),
      inventory.lowStock(),
    ])
      .then(([k, d, tp, pm, s, low]) => {
        setKpis(k);
        setSeries(d);
        setTopProducts(tp);
        setPayments(pm);
        setSummary(s);
        setLowStock(low);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, [days]);

  useEffect(load, [load]);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Business performance at a glance"
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

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatTile label="Revenue" kpi={kpis?.revenue} format={money} />
        <StatTile label="Profit" kpi={kpis?.profit} format={money} />
        <StatTile label="Orders" kpi={kpis?.orders} />
        <StatTile
          label="Avg order value"
          kpi={kpis?.avg_order_value}
          format={money}
        />
      </section>

      <section className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <CountTile label="Products" value={summary?.total_products} />
        <CountTile
          label="Low stock"
          value={summary?.low_stock_count}
          tone="warning"
        />
        <CountTile
          label="Out of stock"
          value={summary?.out_of_stock_count}
          tone="critical"
        />
        <CountTile label="Customers" value={summary?.total_customers} />
      </section>

      <section className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ChartCard
            title="Revenue & profit"
            subtitle={`Daily totals over the last ${days} days`}
          >
            {loading ? (
              <div className="h-72 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
            ) : (
              <RevenueProfitChart data={series} />
            )}
          </ChartCard>
        </div>

        <ChartCard title="Payment mix" subtitle="Share of revenue by method">
          {loading ? (
            <div className="h-32 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
          ) : (
            <PaymentMixBar data={payments} />
          )}
        </ChartCard>
      </section>

      <section className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Top products" subtitle="By units sold">
          {loading ? (
            <div className="h-72 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
          ) : topProducts.length === 0 ? (
            <EmptyState>No sales in this period.</EmptyState>
          ) : (
            <TopProductsChart data={topProducts} />
          )}
        </ChartCard>

        <ChartCard title="Low stock" subtitle="Reorder soon">
          {loading ? (
            <div className="h-40 animate-pulse rounded-xl bg-gray-100 dark:bg-gray-900" />
          ) : lowStock.length === 0 ? (
            <EmptyState>Nothing low on stock. 🎉</EmptyState>
          ) : (
            <div className="max-h-72 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-gray-500 dark:text-gray-400">
                  <tr>
                    <th className="pb-2 font-medium">Product</th>
                    <th className="pb-2 font-medium">In stock</th>
                    <th className="pb-2 font-medium">Shortfall</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {lowStock.map(({ product, shortfall }) => (
                    <tr key={product.id} className="text-gray-800 dark:text-gray-200">
                      <td className="py-2">{product.name}</td>
                      <td className="py-2 tabular-nums">{product.stock_quantity}</td>
                      <td className="py-2">
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 tabular-nums dark:bg-amber-950/60 dark:text-amber-300">
                          {shortfall}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </ChartCard>
      </section>
    </div>
  );
}
