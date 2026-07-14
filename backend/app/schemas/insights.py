"""Insight schemas: worst sellers, dead stock, frequently-bought-together,
and rule-based forecasting.

Every recommendation carries a plain-language `reason`, per the design docs
(the AI must explain WHY, never just show data). Forecasts carry a `confidence`
label because the method is a moving average, not a trained model.
"""
from datetime import date
from enum import Enum

from pydantic import BaseModel


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# --- Worst sellers ------------------------------------------------------


class WorstSeller(BaseModel):
    product_id: int
    name: str
    sku: str
    units_sold: int
    revenue: float
    stock_quantity: int


# --- Dead stock ---------------------------------------------------------


class DeadStockItem(BaseModel):
    product_id: int
    name: str
    sku: str
    stock_quantity: int
    days_since_last_sale: int | None  # None = never sold
    capital_tied_up: float  # stock_quantity * purchase_price
    reason: str


# --- Frequently bought together ----------------------------------------


class ProductPair(BaseModel):
    product_a_id: int
    product_a_name: str
    product_b_id: int
    product_b_name: str
    together_count: int
    support: float  # share of all sales containing both
    confidence_a_to_b: float  # P(B in basket | A in basket)
    confidence_b_to_a: float


class FrequentlyBoughtTogether(BaseModel):
    enough_data: bool
    total_sales: int
    min_sales_required: int
    pairs: list[ProductPair]


# --- Forecast -----------------------------------------------------------


class ProductForecast(BaseModel):
    product_id: int
    name: str
    sku: str
    stock_quantity: int
    avg_daily_demand: float
    days_of_stock_left: float | None  # None = no demand (won't run out)
    projected_stockout_date: date | None
    recommended_reorder_qty: int
    confidence: Confidence
    reason: str
