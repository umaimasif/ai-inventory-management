"""Analytics: KPIs, time series, top-N breakdowns, and the daily report.

Aggregation happens in Python over a bounded date window rather than in SQL.
Reason: grouping by calendar day differs between SQLite (`date()`) and
PostgreSQL (`CAST(... AS date)`), and the sale volumes in scope here are small.
Move to SQL/pandas aggregation if the window ever grows large.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from app.models.sale import Sale
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.analytics import (
    AnalyticsKpis,
    DailyPoint,
    DailyReport,
    KpiValue,
    PaymentSlice,
    TopCategory,
    TopProduct,
)


def _f(value) -> float:
    """Coerce Decimal/None from the DB into a plain float."""
    return float(value or 0)


def _change_pct(current: float, previous: float) -> float | None:
    """Percent change vs the previous period. None when previous is zero."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def _kpi(current: float, previous: float) -> KpiValue:
    return KpiValue(
        current=round(current, 2),
        previous=round(previous, 2),
        change_pct=_change_pct(current, previous),
    )


class _Totals:
    """Running totals for a set of sales."""

    def __init__(self) -> None:
        self.revenue = 0.0
        self.profit = 0.0
        self.orders = 0
        self.units = 0

    def add(self, sale: Sale) -> None:
        self.revenue += _f(sale.total_amount)
        self.profit += _f(sale.total_profit)
        self.orders += 1
        self.units += sum(item.quantity for item in sale.items)

    @property
    def avg_order_value(self) -> float:
        return self.revenue / self.orders if self.orders else 0.0


class AnalyticsService:
    def __init__(self, sales: SaleRepository, products: ProductRepository) -> None:
        self._sales = sales
        self._products = products

    # --- helpers --------------------------------------------------------

    @staticmethod
    def _day_bounds(day: date) -> tuple[datetime, datetime]:
        """[midnight of day, midnight of next day)."""
        start = datetime.combine(day, time.min)
        return start, start + timedelta(days=1)

    def _sales_in_window(self, start_day: date, end_day_exclusive: date) -> list[Sale]:
        start = datetime.combine(start_day, time.min)
        end = datetime.combine(end_day_exclusive, time.min)
        return self._sales.list_between(start, end)

    @staticmethod
    def _sale_day(sale: Sale) -> date:
        return sale.created_at.date()

    # --- KPIs -----------------------------------------------------------

    def kpis(self, days: int, today: date | None = None) -> AnalyticsKpis:
        """Totals for the last `days` days vs the `days` before that."""
        today = today or date.today()
        current_start = today - timedelta(days=days - 1)
        tomorrow = today + timedelta(days=1)
        previous_start = current_start - timedelta(days=days)

        current = _Totals()
        for sale in self._sales_in_window(current_start, tomorrow):
            current.add(sale)

        previous = _Totals()
        for sale in self._sales_in_window(previous_start, current_start):
            previous.add(sale)

        return AnalyticsKpis(
            days=days,
            revenue=_kpi(current.revenue, previous.revenue),
            profit=_kpi(current.profit, previous.profit),
            orders=_kpi(current.orders, previous.orders),
            units_sold=_kpi(current.units, previous.units),
            avg_order_value=_kpi(current.avg_order_value, previous.avg_order_value),
        )

    # --- Time series ----------------------------------------------------

    def daily_series(self, days: int, today: date | None = None) -> list[DailyPoint]:
        """Revenue/profit/orders per calendar day, zero-filled across the window."""
        today = today or date.today()
        start_day = today - timedelta(days=days - 1)

        buckets: dict[date, _Totals] = {
            start_day + timedelta(days=i): _Totals() for i in range(days)
        }

        for sale in self._sales_in_window(start_day, today + timedelta(days=1)):
            bucket = buckets.get(self._sale_day(sale))
            if bucket is not None:
                bucket.add(sale)

        return [
            DailyPoint(
                day=day,
                revenue=round(t.revenue, 2),
                profit=round(t.profit, 2),
                orders=t.orders,
                units=t.units,
            )
            for day, t in sorted(buckets.items())
        ]

    # --- Breakdowns -----------------------------------------------------

    def top_products(
        self, days: int, limit: int = 10, today: date | None = None
    ) -> list[TopProduct]:
        today = today or date.today()
        start_day = today - timedelta(days=days - 1)

        units: dict[int, int] = defaultdict(int)
        revenue: dict[int, float] = defaultdict(float)
        profit: dict[int, float] = defaultdict(float)
        meta: dict[int, tuple[str, str]] = {}

        for sale in self._sales_in_window(start_day, today + timedelta(days=1)):
            for item in sale.items:
                pid = item.product_id
                units[pid] += item.quantity
                revenue[pid] += _f(item.line_total)
                profit[pid] += _f(item.line_profit)
                if pid not in meta and item.product is not None:
                    meta[pid] = (item.product.name, item.product.sku)

        rows = [
            TopProduct(
                product_id=pid,
                name=meta.get(pid, ("(deleted)", "—"))[0],
                sku=meta.get(pid, ("(deleted)", "—"))[1],
                units_sold=units[pid],
                revenue=round(revenue[pid], 2),
                profit=round(profit[pid], 2),
            )
            for pid in units
        ]
        rows.sort(key=lambda r: (r.units_sold, r.revenue), reverse=True)
        return rows[:limit]

    def top_categories(
        self, days: int, limit: int = 10, today: date | None = None
    ) -> list[TopCategory]:
        today = today or date.today()
        start_day = today - timedelta(days=days - 1)

        units: dict[int | None, int] = defaultdict(int)
        revenue: dict[int | None, float] = defaultdict(float)
        profit: dict[int | None, float] = defaultdict(float)
        names: dict[int | None, str] = {}

        for sale in self._sales_in_window(start_day, today + timedelta(days=1)):
            for item in sale.items:
                product = item.product
                cid = product.category_id if product else None
                units[cid] += item.quantity
                revenue[cid] += _f(item.line_total)
                profit[cid] += _f(item.line_profit)
                if cid not in names:
                    category = getattr(product, "category", None) if product else None
                    names[cid] = category.name if category else "Uncategorized"

        rows = [
            TopCategory(
                category_id=cid,
                name=names.get(cid, "Uncategorized"),
                units_sold=units[cid],
                revenue=round(revenue[cid], 2),
                profit=round(profit[cid], 2),
            )
            for cid in units
        ]
        rows.sort(key=lambda r: r.revenue, reverse=True)
        return rows[:limit]

    def payment_mix(self, days: int, today: date | None = None) -> list[PaymentSlice]:
        today = today or date.today()
        start_day = today - timedelta(days=days - 1)

        orders: dict[str, int] = defaultdict(int)
        revenue: dict[str, float] = defaultdict(float)

        for sale in self._sales_in_window(start_day, today + timedelta(days=1)):
            orders[sale.payment_method] += 1
            revenue[sale.payment_method] += _f(sale.total_amount)

        rows = [
            PaymentSlice(
                payment_method=method,
                orders=orders[method],
                revenue=round(revenue[method], 2),
            )
            for method in orders
        ]
        rows.sort(key=lambda r: r.revenue, reverse=True)
        return rows

    # --- Daily report ---------------------------------------------------

    def daily_report(self, day: date | None = None) -> DailyReport:
        """One day's business summary — the basis for the future morning report."""
        day = day or date.today()
        start, end = self._day_bounds(day)

        totals = _Totals()
        for sale in self._sales.list_between(start, end):
            totals.add(sale)

        return DailyReport(
            day=day,
            revenue=round(totals.revenue, 2),
            profit=round(totals.profit, 2),
            orders=totals.orders,
            units_sold=totals.units,
            top_products=self.top_products(days=1, limit=5, today=day),
            low_stock_count=len(self._products.list_low_stock()),
            out_of_stock_count=self._products.count_out_of_stock(),
        )
