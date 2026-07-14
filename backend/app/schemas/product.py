"""Product schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(min_length=1, max_length=60)
    barcode: str | None = Field(default=None, max_length=60)
    category_id: int | None = None
    supplier_id: int | None = None
    purchase_price: float = Field(default=0, ge=0)
    selling_price: float = Field(default=0, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    barcode: str | None = Field(default=None, max_length=60)
    category_id: int | None = None
    supplier_id: int | None = None
    purchase_price: float | None = Field(default=None, ge=0)
    selling_price: float | None = Field(default=None, ge=0)
    min_stock_level: int | None = Field(default=None, ge=0)
    reorder_point: int | None = Field(default=None, ge=0)
    safety_stock: int | None = Field(default=None, ge=0)


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class StockAdjust(BaseModel):
    """Add (positive) or remove (negative) stock, e.g. restock or correction."""

    delta: int = Field(description="Change in units; positive adds, negative removes")
