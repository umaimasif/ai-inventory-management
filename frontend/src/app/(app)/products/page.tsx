"use client";

import { useEffect, useState, type FormEvent } from "react";

import { PageHeader, PrimaryButton } from "@/components/app-shell";
import {
  Button,
  EmptyState,
  ErrorText,
  Field,
  GhostButton,
  Modal,
  Select,
  money,
} from "@/components/ui";
import { ApiError } from "@/lib/api";
import { categories, products, suppliers } from "@/lib/resources";
import type { Category, Product, Supplier } from "@/lib/types";

const BLANK = {
  name: "",
  sku: "",
  barcode: "",
  category_id: "",
  supplier_id: "",
  purchase_price: "0",
  selling_price: "0",
  stock_quantity: "0",
  min_stock_level: "0",
  reorder_point: "0",
  safety_stock: "0",
};

export default function ProductsPage() {
  const [rows, setRows] = useState<Product[]>([]);
  const [cats, setCats] = useState<Category[]>([]);
  const [sups, setSups] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState({ ...BLANK });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reload() {
    setLoading(true);
    Promise.all([products.list(), categories.list(), suppliers.list()])
      .then(([p, c, s]) => {
        setRows(p);
        setCats(c);
        setSups(s);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }

  useEffect(reload, []);

  function set(field: keyof typeof BLANK, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function openCreate() {
    setEditing(null);
    setForm({ ...BLANK });
    setError(null);
    setOpen(true);
  }

  function openEdit(row: Product) {
    setEditing(row);
    setForm({
      name: row.name,
      sku: row.sku,
      barcode: row.barcode ?? "",
      category_id: row.category_id?.toString() ?? "",
      supplier_id: row.supplier_id?.toString() ?? "",
      purchase_price: String(row.purchase_price),
      selling_price: String(row.selling_price),
      stock_quantity: String(row.stock_quantity),
      min_stock_level: String(row.min_stock_level),
      reorder_point: String(row.reorder_point),
      safety_stock: String(row.safety_stock),
    });
    setError(null);
    setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const num = (v: string) => Number(v) || 0;
      const base = {
        name: form.name,
        sku: form.sku,
        barcode: form.barcode || null,
        category_id: form.category_id ? Number(form.category_id) : null,
        supplier_id: form.supplier_id ? Number(form.supplier_id) : null,
        purchase_price: num(form.purchase_price),
        selling_price: num(form.selling_price),
        min_stock_level: num(form.min_stock_level),
        reorder_point: num(form.reorder_point),
        safety_stock: num(form.safety_stock),
      };
      if (editing) {
        // stock_quantity is managed via restock/audit, not edited directly.
        await products.update(editing.id, base);
      } else {
        await products.create({ ...base, stock_quantity: num(form.stock_quantity) });
      }
      setOpen(false);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function restock(row: Product) {
    const raw = prompt(`Restock "${row.name}" — units to add (negative to remove):`, "0");
    if (raw === null) return;
    const delta = Number(raw);
    if (!Number.isFinite(delta) || delta === 0) return;
    try {
      await products.adjustStock(row.id, delta);
      reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Adjust failed.");
    }
  }

  async function remove(row: Product) {
    if (!confirm(`Delete product "${row.name}"?`)) return;
    try {
      await products.remove(row.id);
      reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  const catName = (id: number | null) =>
    id ? (cats.find((c) => c.id === id)?.name ?? "—") : "—";

  return (
    <div>
      <PageHeader
        title="Products"
        subtitle="Your catalog and stock levels"
        action={<PrimaryButton onClick={openCreate}>+ New product</PrimaryButton>}
      />

      {loading ? (
        <EmptyState>Loading…</EmptyState>
      ) : rows.length === 0 ? (
        <EmptyState>No products yet. Add your first product.</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">SKU</th>
                <th className="px-4 py-2 font-medium">Category</th>
                <th className="px-4 py-2 font-medium">Stock</th>
                <th className="px-4 py-2 font-medium">Buy</th>
                <th className="px-4 py-2 font-medium">Sell</th>
                <th className="px-4 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {rows.map((row) => {
                const low =
                  row.stock_quantity <=
                  Math.max(row.reorder_point, row.min_stock_level);
                return (
                  <tr key={row.id} className="text-gray-800 dark:text-gray-200">
                    <td className="px-4 py-2 font-medium">{row.name}</td>
                    <td className="px-4 py-2 text-gray-500">{row.sku}</td>
                    <td className="px-4 py-2 text-gray-500">
                      {catName(row.category_id)}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={
                          low
                            ? "rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : ""
                        }
                      >
                        {row.stock_quantity}
                      </span>
                    </td>
                    <td className="px-4 py-2">{money(row.purchase_price)}</td>
                    <td className="px-4 py-2">{money(row.selling_price)}</td>
                    <td className="px-4 py-2 text-right whitespace-nowrap">
                      <GhostButton onClick={() => restock(row)}>Restock</GhostButton>
                      <GhostButton onClick={() => openEdit(row)}>Edit</GhostButton>
                      <GhostButton tone="danger" onClick={() => remove(row)}>
                        Delete
                      </GhostButton>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        title={editing ? "Edit product" : "New product"}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={submit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Name"
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              required
            />
            <Field
              label="SKU"
              value={form.sku}
              onChange={(e) => set("sku", e.target.value)}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Select
              label="Category"
              value={form.category_id}
              onChange={(e) => set("category_id", e.target.value)}
            >
              <option value="">— none —</option>
              {cats.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
            <Select
              label="Supplier"
              value={form.supplier_id}
              onChange={(e) => set("supplier_id", e.target.value)}
            >
              <option value="">— none —</option>
              {sups.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Purchase price"
              type="number"
              step="0.01"
              min="0"
              value={form.purchase_price}
              onChange={(e) => set("purchase_price", e.target.value)}
            />
            <Field
              label="Selling price"
              type="number"
              step="0.01"
              min="0"
              value={form.selling_price}
              onChange={(e) => set("selling_price", e.target.value)}
            />
          </div>
          {!editing && (
            <Field
              label="Initial stock"
              type="number"
              min="0"
              value={form.stock_quantity}
              onChange={(e) => set("stock_quantity", e.target.value)}
            />
          )}
          <div className="grid grid-cols-3 gap-3">
            <Field
              label="Min stock"
              type="number"
              min="0"
              value={form.min_stock_level}
              onChange={(e) => set("min_stock_level", e.target.value)}
            />
            <Field
              label="Reorder point"
              type="number"
              min="0"
              value={form.reorder_point}
              onChange={(e) => set("reorder_point", e.target.value)}
            />
            <Field
              label="Safety stock"
              type="number"
              min="0"
              value={form.safety_stock}
              onChange={(e) => set("safety_stock", e.target.value)}
            />
          </div>
          <ErrorText>{error}</ErrorText>
          <Button disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
        </form>
      </Modal>
    </div>
  );
}
