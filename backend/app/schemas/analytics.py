"""Analytics schemas: KPIs, time series, top-N breakdowns, daily report."""
from datetime import date

from pydantic import BaseModel


class KpiValue(BaseModel):
    """A metric for the current period, with change vs the previous period."""

    current: float
    previous: float
    change_pct: float | None = None  # None when previous == 0 (undefined)


class AnalyticsKpis(BaseModel):
    """Headline KPIs over a window, compared against the preceding window."""

    days: int
    revenue: KpiValue
    profit: KpiValue
    orders: KpiValue
    units_sold: KpiValue
    avg_order_value: KpiValue


class DailyPoint(BaseModel):
    """One day of the revenue/profit series."""

    day: date
    revenue: float
    profit: float
    orders: int
    units: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    sku: str
    units_sold: int
    revenue: float
    profit: float


class TopCategory(BaseModel):
    category_id: int | None
    name: str
    units_sold: int
    revenue: float
    profit: float


class PaymentSlice(BaseModel):
    payment_method: str
    orders: int
    revenue: float


class DailyReport(BaseModel):
    """A single day's business summary (basis for the future morning report)."""

    day: date
    revenue: float
    profit: float
    orders: int
    units_sold: int
    top_products: list[TopProduct]
    low_stock_count: int
    out_of_stock_count: int
