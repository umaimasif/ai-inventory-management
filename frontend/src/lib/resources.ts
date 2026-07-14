// Typed API clients for Phase 2 resources. All calls are authenticated.

import { apiFetch } from "@/lib/api";
import type {
  AgentReport,
  Alert,
  AnalyticsKpis,
  Category,
  ChatResponse,
  Customer,
  CustomerSegments,
  DailyPoint,
  DailyReport,
  DashboardSummary,
  DeadStockItem,
  FrequentlyBoughtTogether,
  LowStockItem,
  MorningReport,
  PaymentSlice,
  Product,
  ProductForecast,
  Recommendation,
  Sale,
  Supplier,
  TopCategory,
  TopProduct,
  WorstSeller,
} from "@/lib/types";

// --- Categories ---------------------------------------------------------

export const categories = {
  list: () => apiFetch<Category[]>("/api/categories", { auth: true }),
  create: (body: { name: string; description?: string | null }) =>
    apiFetch<Category>("/api/categories", { method: "POST", body, auth: true }),
  update: (id: number, body: Partial<{ name: string; description: string | null }>) =>
    apiFetch<Category>(`/api/categories/${id}`, { method: "PUT", body, auth: true }),
  remove: (id: number) =>
    apiFetch<void>(`/api/categories/${id}`, { method: "DELETE", auth: true }),
};

// --- Suppliers ----------------------------------------------------------

type SupplierBody = {
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
};

export const suppliers = {
  list: () => apiFetch<Supplier[]>("/api/suppliers", { auth: true }),
  create: (body: SupplierBody) =>
    apiFetch<Supplier>("/api/suppliers", { method: "POST", body, auth: true }),
  update: (id: number, body: Partial<SupplierBody>) =>
    apiFetch<Supplier>(`/api/suppliers/${id}`, { method: "PUT", body, auth: true }),
  remove: (id: number) =>
    apiFetch<void>(`/api/suppliers/${id}`, { method: "DELETE", auth: true }),
};

// --- Customers ----------------------------------------------------------

type CustomerBody = {
  name: string;
  phone?: string | null;
  email?: string | null;
};

export const customers = {
  list: () => apiFetch<Customer[]>("/api/customers", { auth: true }),
  create: (body: CustomerBody) =>
    apiFetch<Customer>("/api/customers", { method: "POST", body, auth: true }),
  update: (id: number, body: Partial<CustomerBody>) =>
    apiFetch<Customer>(`/api/customers/${id}`, { method: "PUT", body, auth: true }),
  remove: (id: number) =>
    apiFetch<void>(`/api/customers/${id}`, { method: "DELETE", auth: true }),
};

// --- Products -----------------------------------------------------------

export type ProductBody = {
  name: string;
  sku: string;
  barcode?: string | null;
  category_id?: number | null;
  supplier_id?: number | null;
  purchase_price?: number;
  selling_price?: number;
  stock_quantity?: number;
  min_stock_level?: number;
  reorder_point?: number;
  safety_stock?: number;
};

export const products = {
  list: () => apiFetch<Product[]>("/api/products", { auth: true }),
  create: (body: ProductBody) =>
    apiFetch<Product>("/api/products", { method: "POST", body, auth: true }),
  update: (id: number, body: Partial<ProductBody>) =>
    apiFetch<Product>(`/api/products/${id}`, { method: "PUT", body, auth: true }),
  adjustStock: (id: number, delta: number) =>
    apiFetch<Product>(`/api/products/${id}/adjust-stock`, {
      method: "POST",
      body: { delta },
      auth: true,
    }),
  remove: (id: number) =>
    apiFetch<void>(`/api/products/${id}`, { method: "DELETE", auth: true }),
};

// --- Sales --------------------------------------------------------------

export const sales = {
  list: () => apiFetch<Sale[]>("/api/sales", { auth: true }),
  create: (body: {
    customer_id?: number | null;
    payment_method?: string;
    items: { product_id: number; quantity: number }[];
  }) => apiFetch<Sale>("/api/sales", { method: "POST", body, auth: true }),
};

// --- Inventory / dashboard ---------------------------------------------

export const inventory = {
  summary: () =>
    apiFetch<DashboardSummary>("/api/inventory/summary", { auth: true }),
  lowStock: () =>
    apiFetch<LowStockItem[]>("/api/inventory/low-stock", { auth: true }),
};

// --- Analytics ----------------------------------------------------------

export const analytics = {
  kpis: (days: number) =>
    apiFetch<AnalyticsKpis>(`/api/analytics/kpis?days=${days}`, { auth: true }),
  daily: (days: number) =>
    apiFetch<DailyPoint[]>(`/api/analytics/daily?days=${days}`, { auth: true }),
  topProducts: (days: number, limit = 8) =>
    apiFetch<TopProduct[]>(
      `/api/analytics/top-products?days=${days}&limit=${limit}`,
      { auth: true },
    ),
  topCategories: (days: number, limit = 8) =>
    apiFetch<TopCategory[]>(
      `/api/analytics/top-categories?days=${days}&limit=${limit}`,
      { auth: true },
    ),
  paymentMix: (days: number) =>
    apiFetch<PaymentSlice[]>(`/api/analytics/payment-mix?days=${days}`, {
      auth: true,
    }),
  dailyReport: (day?: string) =>
    apiFetch<DailyReport>(
      `/api/analytics/daily-report${day ? `?day=${day}` : ""}`,
      { auth: true },
    ),
};

// --- Insights & forecasting (Phase 4) -----------------------------------

export const insights = {
  worstSellers: (days: number, limit = 10) =>
    apiFetch<WorstSeller[]>(
      `/api/insights/worst-sellers?days=${days}&limit=${limit}`,
      { auth: true },
    ),
  deadStock: (days: number) =>
    apiFetch<DeadStockItem[]>(`/api/insights/dead-stock?days=${days}`, {
      auth: true,
    }),
  frequentlyBoughtTogether: (days: number, limit = 10) =>
    apiFetch<FrequentlyBoughtTogether>(
      `/api/insights/frequently-bought-together?days=${days}&limit=${limit}`,
      { auth: true },
    ),
  forecast: (days: number) =>
    apiFetch<ProductForecast[]>(`/api/insights/forecast?days=${days}`, {
      auth: true,
    }),
};

// --- AI agents (Phase 5) ------------------------------------------------

export const agents = {
  inventory: () => apiFetch<AgentReport>("/api/agents/inventory", { auth: true }),
  sales: (days: number) =>
    apiFetch<AgentReport>(`/api/agents/sales?days=${days}`, { auth: true }),
  customers: () =>
    apiFetch<CustomerSegments>("/api/agents/customers", { auth: true }),
  recommendations: (days: number) =>
    apiFetch<Recommendation[]>(`/api/agents/recommendations?days=${days}`, {
      auth: true,
    }),
  alerts: (days: number) =>
    apiFetch<Alert[]>(`/api/agents/alerts?days=${days}`, { auth: true }),
  report: (day?: string) =>
    apiFetch<MorningReport>(
      `/api/agents/report${day ? `?day=${day}` : ""}`,
      { auth: true },
    ),
  ask: (question: string) =>
    apiFetch<ChatResponse>("/api/agents/assistant/chat", {
      method: "POST",
      body: { question },
      auth: true,
    }),
};
