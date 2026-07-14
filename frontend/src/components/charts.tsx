"use client";

// Chart components. Colors come from the validated palette exposed as CSS
// custom properties on `.viz-root` (see globals.css), so light/dark swap in
// one place and SVG marks reference roles, not raw hex.
//
// Rules enforced here:
//  - one y-axis per chart, never dual-axis
//  - categorical hues assigned in fixed slot order, never cycled
//  - legend present for >= 2 series; single-series charts get none
//  - hover tooltip on every plot
//  - recessive grid/axes, 2px lines, 8px markers, 4px rounded bar ends

import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { money } from "@/components/ui";
import type { DailyPoint, PaymentSlice, TopProduct } from "@/lib/types";

const AXIS = "var(--viz-muted)";
const GRID = "var(--viz-grid)";
const SERIES_1 = "var(--series-1)";
const SERIES_2 = "var(--series-2)";

/** Card surface around a chart, with its title. */
export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="viz-root rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-950">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {subtitle && (
          <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );
}

/** Shared tooltip chrome so every chart's hover layer looks the same. */
function tooltipProps() {
  return {
    contentStyle: {
      background: "var(--viz-surface)",
      border: "1px solid var(--viz-grid)",
      borderRadius: "0.75rem",
      fontSize: "0.75rem",
      color: "var(--viz-text)",
    },
    labelStyle: { color: "var(--viz-text-secondary)" },
    cursor: { stroke: "var(--viz-axis)", strokeWidth: 1 },
  };
}

const shortDay = (iso: string) =>
  new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });

/**
 * Revenue vs profit over time. Two categorical series, both in currency —
 * so they legitimately share one axis. A legend plus the tooltip carry
 * identity, satisfying the relief rule for the lower-contrast aqua.
 */
export function RevenueProfitChart({ data }: { data: DailyPoint[] }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="0" vertical={false} />
          <XAxis
            dataKey="day"
            tickFormatter={shortDay}
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "var(--viz-axis)" }}
            minTickGap={24}
          />
          <YAxis
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={64}
          />
          <Tooltip
            {...tooltipProps()}
            labelFormatter={(v) => shortDay(String(v))}
            formatter={(value, name) => [money(Number(value ?? 0)), String(name)]}
          />
          <Legend
            iconType="plainline"
            wrapperStyle={{ fontSize: "0.75rem", color: "var(--viz-text-secondary)" }}
          />
          <Line
            type="monotone"
            dataKey="revenue"
            name="Revenue"
            stroke={SERIES_1}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--viz-surface)" }}
          />
          <Line
            type="monotone"
            dataKey="profit"
            name="Profit"
            stroke={SERIES_2}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--viz-surface)" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Top products by units sold. Single series → magnitude, so one hue and
 * no legend (the title names the measure). Horizontal bars because product
 * names are long.
 */
export function TopProductsChart({ data }: { data: TopProduct[] }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 24, bottom: 0, left: 8 }}
          barCategoryGap="28%"
        >
          <CartesianGrid stroke={GRID} horizontal={false} />
          <XAxis
            type="number"
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "var(--viz-axis)" }}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke={AXIS}
            tick={{ fill: AXIS, fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={110}
          />
          <Tooltip
            {...tooltipProps()}
            cursor={{ fill: "var(--viz-grid)", fillOpacity: 0.4 }}
            formatter={(value) => [`${Number(value ?? 0)} units`, "Sold"]}
          />
          <Bar
            dataKey="units_sold"
            fill={SERIES_1}
            radius={[0, 4, 4, 0]}
            maxBarSize={22}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Payment method share of revenue. Part-to-whole across a small, fixed set
 * of methods — a stacked horizontal bar, not a pie. Values are direct-labeled
 * in the accompanying list, so color never carries meaning alone.
 */
export function PaymentMixBar({ data }: { data: PaymentSlice[] }) {
  const total = data.reduce((sum, slice) => sum + slice.revenue, 0);
  const SLOTS = [SERIES_1, SERIES_2, "var(--series-3)"];

  if (total === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">
        No sales in this period.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {/* 2px surface gap between adjacent fills. */}
      <div className="flex h-4 w-full gap-[2px] overflow-hidden rounded-full">
        {data.map((slice, i) => (
          <div
            key={slice.payment_method}
            style={{
              width: `${(slice.revenue / total) * 100}%`,
              background: SLOTS[i % SLOTS.length],
            }}
            title={`${slice.payment_method}: ${money(slice.revenue)}`}
          />
        ))}
      </div>
      <ul className="space-y-1.5 text-sm">
        {data.map((slice, i) => (
          <li
            key={slice.payment_method}
            className="flex items-center justify-between"
          >
            <span className="flex items-center gap-2 text-gray-700 capitalize dark:text-gray-300">
              <span
                aria-hidden
                className="inline-block h-2.5 w-2.5 rounded-full"
                style={{ background: SLOTS[i % SLOTS.length] }}
              />
              {slice.payment_method}
            </span>
            <span className="text-gray-500 tabular-nums dark:text-gray-400">
              {money(slice.revenue)} · {Math.round((slice.revenue / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
