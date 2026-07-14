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
} from "@/components/ui";
import { ApiError } from "@/lib/api";
import { suppliers } from "@/lib/resources";
import type { Supplier } from "@/lib/types";

const BLANK = { name: "", contact_name: "", email: "", phone: "", address: "" };

export default function SuppliersPage() {
  const [rows, setRows] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [form, setForm] = useState({ ...BLANK });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reload() {
    setLoading(true);
    suppliers
      .list()
      .then(setRows)
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

  function openEdit(row: Supplier) {
    setEditing(row);
    setForm({
      name: row.name,
      contact_name: row.contact_name ?? "",
      email: row.email ?? "",
      phone: row.phone ?? "",
      address: row.address ?? "",
    });
    setError(null);
    setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const body = {
        name: form.name,
        contact_name: form.contact_name || null,
        email: form.email || null,
        phone: form.phone || null,
        address: form.address || null,
      };
      if (editing) await suppliers.update(editing.id, body);
      else await suppliers.create(body);
      setOpen(false);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(row: Supplier) {
    if (!confirm(`Delete supplier "${row.name}"?`)) return;
    try {
      await suppliers.remove(row.id);
      reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  return (
    <div>
      <PageHeader
        title="Suppliers"
        subtitle="Vendors you buy stock from"
        action={<PrimaryButton onClick={openCreate}>+ New supplier</PrimaryButton>}
      />

      {loading ? (
        <EmptyState>Loading…</EmptyState>
      ) : rows.length === 0 ? (
        <EmptyState>No suppliers yet.</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Contact</th>
                <th className="px-4 py-2 font-medium">Phone</th>
                <th className="px-4 py-2 font-medium">Email</th>
                <th className="px-4 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {rows.map((row) => (
                <tr key={row.id} className="text-gray-800 dark:text-gray-200">
                  <td className="px-4 py-2 font-medium">{row.name}</td>
                  <td className="px-4 py-2 text-gray-500">{row.contact_name ?? "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{row.phone ?? "—"}</td>
                  <td className="px-4 py-2 text-gray-500">{row.email ?? "—"}</td>
                  <td className="px-4 py-2 text-right">
                    <GhostButton onClick={() => openEdit(row)}>Edit</GhostButton>
                    <GhostButton tone="danger" onClick={() => remove(row)}>
                      Delete
                    </GhostButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={open}
        title={editing ? "Edit supplier" : "New supplier"}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={submit} className="space-y-4">
          <Field
            label="Name"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Contact name"
              value={form.contact_name}
              onChange={(e) => set("contact_name", e.target.value)}
            />
            <Field
              label="Phone"
              value={form.phone}
              onChange={(e) => set("phone", e.target.value)}
            />
          </div>
          <Field
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
          />
          <Field
            label="Address"
            value={form.address}
            onChange={(e) => set("address", e.target.value)}
          />
          <ErrorText>{error}</ErrorText>
          <Button disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
        </form>
      </Modal>
    </div>
  );
}
