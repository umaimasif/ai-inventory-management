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
import { categories } from "@/lib/resources";
import type { Category } from "@/lib/types";

export default function CategoriesPage() {
  const [rows, setRows] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reload() {
    setLoading(true);
    categories
      .list()
      .then(setRows)
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }

  useEffect(reload, []);

  function openCreate() {
    setEditing(null);
    setName("");
    setDescription("");
    setError(null);
    setOpen(true);
  }

  function openEdit(row: Category) {
    setEditing(row);
    setName(row.name);
    setDescription(row.description ?? "");
    setError(null);
    setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const body = { name, description: description || null };
      if (editing) await categories.update(editing.id, body);
      else await categories.create(body);
      setOpen(false);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(row: Category) {
    if (!confirm(`Delete category "${row.name}"?`)) return;
    try {
      await categories.remove(row.id);
      reload();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  return (
    <div>
      <PageHeader
        title="Categories"
        subtitle="Organize your products"
        action={<PrimaryButton onClick={openCreate}>+ New category</PrimaryButton>}
      />

      {loading ? (
        <EmptyState>Loading…</EmptyState>
      ) : rows.length === 0 ? (
        <EmptyState>No categories yet. Create your first one.</EmptyState>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left text-gray-500 dark:bg-gray-900 dark:text-gray-400">
              <tr>
                <th className="px-4 py-2 font-medium">Name</th>
                <th className="px-4 py-2 font-medium">Description</th>
                <th className="px-4 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {rows.map((row) => (
                <tr key={row.id} className="text-gray-800 dark:text-gray-200">
                  <td className="px-4 py-2 font-medium">{row.name}</td>
                  <td className="px-4 py-2 text-gray-500">
                    {row.description ?? "—"}
                  </td>
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
        title={editing ? "Edit category" : "New category"}
        onClose={() => setOpen(false)}
      >
        <form onSubmit={submit} className="space-y-4">
          <Field
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Field
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <ErrorText>{error}</ErrorText>
          <Button disabled={saving}>{saving ? "Saving…" : "Save"}</Button>
        </form>
      </Modal>
    </div>
  );
}
