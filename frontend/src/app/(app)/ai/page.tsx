"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/app-shell";
import { ChartCard } from "@/components/charts";
import { EmptyState, money } from "@/components/ui";
import { agents } from "@/lib/resources";
import type {
  AgentReport,
  CustomerSegments,
  MorningReport,
  Priority,
  Severity,
} from "@/lib/types";

function SeverityDot({ severity }: { severity: Severity }) {
  const color =
    severity === "critical"
      ? "bg-red-500"
      : severity === "warning"
        ? "bg-amber-500"
        : "bg-gray-400";
  return <span className={`mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full ${color}`} />;
}

function PriorityBadge({ priority }: { priority: Priority }) {
  const cls =
    priority === "high"
      ? "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300"
      : priority === "medium"
        ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
        : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {priority}
    </span>
  );
}

const SEGMENT_LABELS: Record<string, string> = {
  vip: "VIP",
  regular: "Regular",
  new: "New",
  inactive: "Inactive",
};

export default function AiBriefingPage() {
  const [report, setReport] = useState<MorningReport | null>(null);
  const [inventory, setInventory] = useState<AgentReport | null>(null);
  const [sales, setSales] = useState<AgentReport | null>(null);
  const [segments, setSegments] = useState<CustomerSegments | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      agents.report(),
      agents.inventory(),
      agents.sales(30),
      agents.customers(),
    ])
      .then(([r, inv, s, seg]) => {
        setReport(r);
        setInventory(inv);
        setSales(s);
        setSegments(seg);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <PageHeader title="AI Briefing" subtitle="What your agents found today" />
        <EmptyState>Running agents…</EmptyState>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="AI Briefing"
        subtitle="A daily read-out from your seven specialized agents"
      />

      {/* Morning narrative */}
      {report && (
        <div className="mb-4 rounded-2xl border border-indigo-200 bg-indigo-50 p-5 dark:border-indigo-900 dark:bg-indigo-950/40">
          <div className="mb-2 flex items-center gap-2">
            <h2 className="text-base font-semibold text-indigo-900 dark:text-indigo-200">
              Morning report
            </h2>
            <span className="rounded-full bg-indigo-200 px-2 py-0.5 text-xs text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
              {report.llm_used ? "LLM-phrased" : "grounded template"}
            </span>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-sm text-indigo-900 dark:text-indigo-100">
            {report.narrative}
          </pre>
        </div>
      )}

      {/* Alerts */}
      {report && report.alerts.length > 0 && (
        <div className="mb-4">
          <h2 className="mb-2 text-base font-semibold text-gray-900 dark:text-white">
            Smart alerts
          </h2>
          <div className="space-y-2">
            {report.alerts.map((a, i) => (
              <div
                key={i}
                className="flex gap-2 rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-950"
              >
                <SeverityDot severity={a.severity} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {a.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {a.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {/* Recommendations */}
        <ChartCard title="Recommendations" subtitle="From the Recommendation Agent">
          {!report || report.recommendations.length === 0 ? (
            <EmptyState>No recommendations right now.</EmptyState>
          ) : (
            <ul className="space-y-3">
              {report.recommendations.map((r, i) => (
                <li
                  key={i}
                  className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {r.title}
                    </span>
                    <PriorityBadge priority={r.priority} />
                  </div>
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {r.reason}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>

        {/* Customer segments */}
        <ChartCard title="Customer segments" subtitle="From the Customer Intelligence Agent">
          {!segments || segments.customers.length === 0 ? (
            <EmptyState>No customer history yet.</EmptyState>
          ) : (
            <>
              <div className="mb-3 flex flex-wrap gap-2">
                {Object.entries(segments.counts).map(([seg, count]) => (
                  <span
                    key={seg}
                    className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  >
                    {SEGMENT_LABELS[seg] ?? seg}: {count}
                  </span>
                ))}
              </div>
              <table className="w-full text-sm">
                <thead className="text-left text-gray-500 dark:text-gray-400">
                  <tr>
                    <th className="pb-2 font-medium">Customer</th>
                    <th className="pb-2 font-medium">Segment</th>
                    <th className="pb-2 font-medium">Spent</th>
                    <th className="pb-2 font-medium">Orders</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {segments.customers.slice(0, 8).map((c) => (
                    <tr key={c.customer_id} className="text-gray-800 dark:text-gray-200">
                      <td className="py-2">{c.name}</td>
                      <td className="py-2 capitalize">{SEGMENT_LABELS[c.segment] ?? c.segment}</td>
                      <td className="py-2 tabular-nums">{money(c.total_spent)}</td>
                      <td className="py-2 tabular-nums">{c.orders}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </ChartCard>

        {/* Inventory agent findings */}
        <ChartCard title="Inventory Agent" subtitle="Stock health">
          <ul className="space-y-2">
            {inventory?.findings.map((f, i) => (
              <li key={i} className="flex gap-2">
                <SeverityDot severity={f.severity} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {f.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {f.detail}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </ChartCard>

        {/* Sales agent findings */}
        <ChartCard title="Sales Analysis Agent" subtitle="Trends & sellers">
          <ul className="space-y-2">
            {sales?.findings.map((f, i) => (
              <li key={i} className="flex gap-2">
                <SeverityDot severity={f.severity} />
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {f.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {f.detail}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </ChartCard>
      </div>
    </div>
  );
}
