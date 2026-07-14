"""Rule-based inventory forecasting.

Deliberately NOT machine learning. Per the design notes, with limited history a
moving average plus a reorder-point rule is more honest than a trained model.
Every forecast reports a `confidence` derived from how much data backs it, and a
plain-language `reason`. Swap in an ML model once ~60+ days of history exist.
"""
import math
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.insights import Confidence, ProductForecast

# Planning assumptions. Real deployments would source these per-supplier.
LEAD_TIME_DAYS = 7  # time from order to stock on shelf
REVIEW_PERIOD_DAYS = 7  # how often reordering is reviewed

# Confidence thresholds, in distinct days the product actually sold.
HIGH_CONFIDENCE_DAYS = 15
MEDIUM_CONFIDENCE_DAYS = 5


class ForecastService:
    def __init__(self, sales: SaleRepository, products: ProductRepository) -> None:
        self._sales = sales
        self._products = products

    def _demand_by_product(
        self, days: int, today: date
    ) -> tuple[dict[int, int], dict[int, set[date]]]:
        """Units sold and the set of active sale-days, per product, in-window."""
        start = datetime.combine(today - timedelta(days=days - 1), time.min)
        end = datetime.combine(today + timedelta(days=1), time.min)

        units: dict[int, int] = defaultdict(int)
        active_days: dict[int, set[date]] = defaultdict(set)

        for sale in self._sales.list_between(start, end):
            day = sale.created_at.date()
            for item in sale.items:
                units[item.product_id] += item.quantity
                active_days[item.product_id].add(day)

        return units, active_days

    @staticmethod
    def _confidence(active_day_count: int) -> Confidence:
        if active_day_count >= HIGH_CONFIDENCE_DAYS:
            return Confidence.high
        if active_day_count >= MEDIUM_CONFIDENCE_DAYS:
            return Confidence.medium
        return Confidence.low

    def _forecast_one(
        self, product: Product, units_sold: int, active_day_count: int, days: int, today: date
    ) -> ProductForecast:
        avg_daily = units_sold / days if days else 0.0
        confidence = self._confidence(active_day_count)

        if avg_daily <= 0:
            return ProductForecast(
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                stock_quantity=product.stock_quantity,
                avg_daily_demand=0.0,
                days_of_stock_left=None,
                projected_stockout_date=None,
                recommended_reorder_qty=0,
                confidence=Confidence.low,
                reason=(
                    f"No sales in the last {days} days — no demand signal. "
                    f"Do not reorder; review whether to clear existing stock."
                ),
            )

        days_left = product.stock_quantity / avg_daily
        stockout_date = today + timedelta(days=math.floor(days_left))

        # Target stock covers the lead time plus one review period, plus the
        # product's own safety stock. Reorder up to that target.
        cover_days = LEAD_TIME_DAYS + REVIEW_PERIOD_DAYS
        target_stock = avg_daily * cover_days + product.safety_stock
        reorder_qty = max(0, math.ceil(target_stock - product.stock_quantity))

        if reorder_qty > 0:
            reason = (
                f"Selling ~{avg_daily:.1f}/day; about {days_left:.0f} days of stock "
                f"left. To cover the {cover_days}-day lead+review window plus safety "
                f"stock, reorder {reorder_qty} units. Confidence {confidence.value} "
                f"({active_day_count} active sale-days)."
            )
        else:
            reason = (
                f"Selling ~{avg_daily:.1f}/day with about {days_left:.0f} days of "
                f"stock left — enough to cover the {cover_days}-day window. No "
                f"reorder needed yet. Confidence {confidence.value}."
            )

        return ProductForecast(
            product_id=product.id,
            name=product.name,
            sku=product.sku,
            stock_quantity=product.stock_quantity,
            avg_daily_demand=round(avg_daily, 3),
            days_of_stock_left=round(days_left, 1),
            projected_stockout_date=stockout_date,
            recommended_reorder_qty=reorder_qty,
            confidence=confidence,
            reason=reason,
        )

    def forecast(self, days: int = 30, today: date | None = None) -> list[ProductForecast]:
        """Forecast every product, most-urgent (soonest stockout) first."""
        today = today or date.today()
        units, active_days = self._demand_by_product(days, today)

        forecasts = [
            self._forecast_one(
                product,
                units.get(product.id, 0),
                len(active_days.get(product.id, set())),
                days,
                today,
            )
            for product in self._products.list(limit=100000)
        ]

        # Products that will run out soonest come first; no-demand items last.
        def sort_key(f: ProductForecast) -> float:
            return f.days_of_stock_left if f.days_of_stock_left is not None else float("inf")

        forecasts.sort(key=sort_key)
        return forecasts
