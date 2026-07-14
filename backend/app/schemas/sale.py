"""Sale schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    customer_id: int | None = None
    payment_method: str = Field(default="cash", max_length=30)
    items: list[SaleItemCreate] = Field(min_length=1)


class SaleItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: float
    unit_cost: float
    line_total: float
    line_profit: float


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None
    payment_method: str
    total_amount: float
    total_profit: float
    created_at: datetime
    items: list[SaleItemRead]
