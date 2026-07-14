// Shared API types (mirror the backend Pydantic schemas).

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

// --- Phase 2 entities ---------------------------------------------------

export interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  created_at: string;
}

export interface Customer {
  id: number;
  name: string;
  phone: string | null;
  email: string | null;
  is_walkin: boolean;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string | null;
  category_id: number | null;
  supplier_id: number | null;
  purchase_price: number;
  selling_price: number;
  stock_quantity: number;
  min_stock_level: number;
  reorder_point: number;
  safety_stock: number;
  created_at: string;
}

export interface SaleItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  unit_cost: number;
  line_total: number;
  line_profit: number;
}

export interface Sale {
  id: number;
  customer_id: number | null;
  payment_method: string;
  total_amount: number;
  total_profit: number;
  created_at: string;
  items: SaleItem[];
}

export interface LowStockItem {
  product: Product;
  shortfall: number;
}

export interface DashboardSummary {
  total_products: number;
  low_stock_count: number;
  out_of_stock_count: number;
  total_stock_units: number;
  total_customers: number;
  total_sales: number;
}

// --- Phase 3: analytics -------------------------------------------------

export interface KpiValue {
  current: number;
  previous: number;
  change_pct: number | null;
}

export interface AnalyticsKpis {
  days: number;
  revenue: KpiValue;
  profit: KpiValue;
  orders: KpiValue;
  units_sold: KpiValue;
  avg_order_value: KpiValue;
}

export interface DailyPoint {
  day: string;
  revenue: number;
  profit: number;
  orders: number;
  units: number;
}

export interface TopProduct {
  product_id: number;
  name: string;
  sku: string;
  units_sold: number;
  revenue: number;
  profit: number;
}

export interface TopCategory {
  category_id: number | null;
  name: string;
  units_sold: number;
  revenue: number;
  profit: number;
}

export interface PaymentSlice {
  payment_method: string;
  orders: number;
  revenue: number;
}

export interface DailyReport {
  day: string;
  revenue: number;
  profit: number;
  orders: number;
  units_sold: number;
  top_products: TopProduct[];
  low_stock_count: number;
  out_of_stock_count: number;
}

// --- Phase 4: insights & forecasting ------------------------------------

export type Confidence = "low" | "medium" | "high";

export interface WorstSeller {
  product_id: number;
  name: string;
  sku: string;
  units_sold: number;
  revenue: number;
  stock_quantity: number;
}

export interface DeadStockItem {
  product_id: number;
  name: string;
  sku: string;
  stock_quantity: number;
  days_since_last_sale: number | null;
  capital_tied_up: number;
  reason: string;
}

export interface ProductPair {
  product_a_id: number;
  product_a_name: string;
  product_b_id: number;
  product_b_name: string;
  together_count: number;
  support: number;
  confidence_a_to_b: number;
  confidence_b_to_a: number;
}

export interface FrequentlyBoughtTogether {
  enough_data: boolean;
  total_sales: number;
  min_sales_required: number;
  pairs: ProductPair[];
}

export interface ProductForecast {
  product_id: number;
  name: string;
  sku: string;
  stock_quantity: number;
  avg_daily_demand: number;
  days_of_stock_left: number | null;
  projected_stockout_date: string | null;
  recommended_reorder_qty: number;
  confidence: Confidence;
  reason: string;
}

// --- Phase 5: AI agents -------------------------------------------------

export type Severity = "info" | "warning" | "critical";
export type Priority = "low" | "medium" | "high";
export type Segment = "vip" | "regular" | "new" | "inactive";

export interface Finding {
  title: string;
  detail: string;
  severity: Severity;
}

export interface AgentReport {
  agent: string;
  findings: Finding[];
}

export interface Recommendation {
  title: string;
  reason: string;
  priority: Priority;
  category: string;
}

export interface CustomerInsight {
  customer_id: number;
  name: string;
  segment: Segment;
  total_spent: number;
  orders: number;
  days_since_last_purchase: number | null;
  favorite_category: string | null;
  reason: string;
}

export interface CustomerSegments {
  counts: Record<string, number>;
  customers: CustomerInsight[];
}

export interface Alert {
  title: string;
  detail: string;
  severity: Severity;
}

export interface MorningReport {
  report: DailyReport;
  recommendations: Recommendation[];
  alerts: Alert[];
  narrative: string;
  llm_used: boolean;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  grounded_on: Record<string, unknown>;
  llm_used: boolean;
}
