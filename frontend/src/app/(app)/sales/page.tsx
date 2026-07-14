"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader, PrimaryButton } from "@/components/app-shell";
import {
  Button,
  EmptyState,
  ErrorText,
  GhostButton,
  Modal,
  Select,
  money,
} from "@/components/ui";
import { ApiError } from "@/lib/api";
import { customers, products, sales } from "@/lib/resources";
import type { Customer, Product, Sale } from "@/lib/types";

interface Line {
  product_id: string;
  quantity: string;
}

export default function SalesPage() {
  const [rows, setRows] = useState<Sale[]>([]);
  const [prods, setProds] = useState<Product[]>([]);
  const [custs, setCusts] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  const [open, setOpen] = useState(false);
  const [customerId, setCustomerId] = useState("");
  const [payment, setPayment] = useState("cash");
  const [lines, setLines] = useState<Line[]>([{ product_id: "", quantity: "1" }]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reload() {
    setLoading(true);
    Promise.all([sales.list(), products.list(), customers.list()])
      .then(([s, p, c]) => {
        setRows(s);
        setProds(p);
        setCusts(c);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }

  useEffect(reload, []);

  const productById = useMemo(
    () => new Map(prods.map((p) => [p.id, p])),
    [prods],
  );

  const total = useMemo(() => {
    return lines.reduce((sum, line) => {
      const p = productById.get(Number(line.product_id));
      const qty = Number(line.quantity) || 0;
      return sum + (p ? p.selling_price * qty : 0);
    }, 0);
  }, [lines, productById]);

  function openNew() {
    setCustomerId("");
    setPayment("cash");
    setLines([{ product_id: "", quantity: "1" }]);
    setError(null);
    setOpen(true);
  }

  function setLine(idx: number, field: keyof Line, value: string) {
    setLines((ls) => ls.map((l, i) => (i === idx ? { ...l, [field]: value } : l)));
  }

  function addLine() {
    setLines((ls) => [...ls, { product_id: "", quantity: "1" }]);
  }

  function removeLine(idx: number) {
    setLines((ls) => (ls.length === 1 ? ls : ls.filter((_, i) => i !== idx)));
  }

  async function submit() {
    setError(null);
    const items = lines
      .filter((l) => l.product_id && Number(l.quantity) > 0)
      .map((l) => ({ product_id: Number(l.product_id), quantity: Number(l.quantity) }));

    if (items.length === 0) {
      setError("Add at least one product with a quantity.");
      return;
    }

    setSaving(true);
    try {
      await sales.create({
        customer_id: customerId ? Number(customerId) : null,
        payment_method: payment,
        items,
      });
      setOpen(false);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sale failed.");
    } finally {
      setSaving(false);
    }
  }

  const custName = (id: number | null) =>
    id ? (custs.find((c) => c.id === id)?.name ?? `#${id}`) : "Walk-in";

  return (
    <div>
      <PageHeader
        title="Sales"
        subtitle="Record sales and view history"
        action={<PrimaryButton onClick={openNew}>+ New sale</PrimaryButton>}
      />

      {loading ? (
        <EmptyState>Loading…</EmptyState>
      ) : rows.length === 0 ? (
        <EmptyState>No sales recorded yet.</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              <tr>
                <th className="px-4 py-2 font-medium">#</th>
                <th className="px-4 py-2 font-medium">Date</th>
                <th className="px-4 py-2 font-medium">Customer</th>
                <th className="px-4 py-2 font-medium">Items</th>
                <th className="px-4 py-2 font-medium">Payment</th>
                <th className="px-4 py-2 font-medium">Total</th>
                <th className="px-4 py-2 font-medium">Profit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {rows.map((sale) => (
                <tr key={sale.id} className="text-gray-800 dark:text-gray-200">
                  <td className="px-4 py-2">{sale.id}</td>
                  <td className="px-4 py-2 text-gray-500">
                    {new Date(sale.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">{custName(sale.customer_id)}</td>
                  <td className="px-4 py-2 text-gray-500">{sale.items.length}</td>
                  <td className="px-4 py-2 text-gray-500">{sale.payment_method}</td>
                  <td className="px-4 py-2 font-medium">{money(sale.total_amount)}</td>
                  <td className="px-4 py-2 text-emerald-600 dark:text-emerald-400">
                    {money(sale.total_profit)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={open} title="New sale" onClose={() => setOpen(false)}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Customer"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
            >
              <option value="">Walk-in</option>
              {custs
                .filter((c) => !c.is_walkin)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
            </Select>
            <Select
              label="Payment"
              value={payment}
              onChange={(e) => setPayment(e.target.value)}
            >
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="mobile">Mobile</option>
            </Select>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Items
            </p>
            {lines.map((line, idx) => (
              <div key={idx} className="flex items-end gap-2">
                <div className="flex-1">
                  <select
                    value={line.product_id}
                    onChange={(e) => setLine(idx, "product_id", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select product…</option>
                    {prods.map((p) => (
                      <option key={p.id} value={p.id} disabled={p.stock_quantity <= 0}>
                        {p.name} ({p.stock_quantity} in stock)
                      </option>
                    ))}
                  </select>
                </div>
                <input
                  type="number"
                  min="1"
                  value={line.quantity}
                  onChange={(e) => setLine(idx, "quantity", e.target.value)}
                  className="w-20 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                />
                <GhostButton tone="danger" onClick={() => removeLine(idx)}>
                  ✕
                </GhostButton>
              </div>
            ))}
            <GhostButton onClick={addLine}>+ Add item</GhostButton>
          </div>

          <div className="flex items-center justify-between border-t border-gray-200 pt-3 dark:border-gray-800">
            <span className="text-sm text-gray-500">Estimated total</span>
            <span className="text-lg font-semibold text-gray-900 dark:text-white">
              {money(total)}
            </span>
          </div>

          <ErrorText>{error}</ErrorText>
          <Button type="button" disabled={saving} onClick={submit}>
            {saving ? "Recording…" : "Record sale"}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
