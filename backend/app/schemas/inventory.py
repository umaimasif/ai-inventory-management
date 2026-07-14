"""Inventory / dashboard schemas: low-stock, audits, KPI summary."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class StockAuditCreate(BaseModel):
    """Record a physical count for a product."""

    product_id: int
    physical_count: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


class StockAuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    system_count: int
    physical_count: int
    difference: int
    note: str | None
    created_at: datetime


class LowStockItem(BaseModel):
    """A product at or below its reorder point (or min stock level)."""

    product: ProductRead
    shortfall: int


class DashboardSummary(BaseModel):
    """Top-level KPI counts for the dashboard."""

    total_products: int
    low_stock_count: int
    out_of_stock_count: int
    total_stock_units: int
    total_customers: int
    total_sales: int
