"""Insights: worst sellers, dead stock, and market-basket analysis.

Like analytics, aggregation runs in Python over a bounded window — volumes are
small and it stays portable across SQLite/PostgreSQL.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from itertools import combinations

from app.models.sale import Sale
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.insights import (
    DeadStockItem,
    FrequentlyBoughtTogether,
    ProductPair,
    WorstSeller,
)

# A pair analysis is meaningless on a handful of sales — hide it until there
# is enough signal (matches the design note to hide FBT until data grows).
MIN_SALES_FOR_FBT = 20


def _f(value) -> float:
    return float(value or 0)


class InsightsService:
    def __init__(self, sales: SaleRepository, products: ProductRepository) -> None:
        self._sales = sales
        self._products = products

    def _sales_in_window(self, days: int, today: date) -> list[Sale]:
        start = datetime.combine(today - timedelta(days=days - 1), time.min)
        end = datetime.combine(today + timedelta(days=1), time.min)
        return self._sales.list_between(start, end)

    # --- Worst sellers --------------------------------------------------

    def worst_sellers(
        self, days: int, limit: int = 10, today: date | None = None
    ) -> list[WorstSeller]:
        """Lowest units sold over the window, including never-sold products."""
        today = today or date.today()
        units: dict[int, int] = defaultdict(int)
        revenue: dict[int, float] = defaultdict(float)

        for sale in self._sales_in_window(days, today):
            for item in sale.items:
                units[item.product_id] += item.quantity
                revenue[item.product_id] += _f(item.line_total)

        rows = [
            WorstSeller(
                product_id=p.id,
                name=p.name,
                sku=p.sku,
                units_sold=units.get(p.id, 0),
                revenue=round(revenue.get(p.id, 0.0), 2),
                stock_quantity=p.stock_quantity,
            )
            for p in self._products.list(limit=100000)
        ]
        # Lowest sellers first; break ties by higher stock (more capital stuck).
        rows.sort(key=lambda r: (r.units_sold, -r.stock_quantity))
        return rows[:limit]

    # --- Dead stock -----------------------------------------------------

    def dead_stock(
        self, days: int = 30, today: date | None = None
    ) -> list[DeadStockItem]:
        """Products holding stock with no sale in the last `days` days."""
        today = today or date.today()
        cutoff = today - timedelta(days=days - 1)

        # Last sale date per product across ALL history, not just the window.
        last_sold: dict[int, date] = {}
        for sale in self._sales.list(limit=100000):
            day = sale.created_at.date()
            for item in sale.items:
                prev = last_sold.get(item.product_id)
                if prev is None or day > prev:
                    last_sold[item.product_id] = day

        items: list[DeadStockItem] = []
        for product in self._products.list(limit=100000):
            if product.stock_quantity <= 0:
                continue  # no capital tied up; not "dead stock"

            last = last_sold.get(product.id)
            if last is not None and last >= cutoff:
                continue  # sold recently — alive

            days_since = (today - last).days if last is not None else None
            capital = round(product.stock_quantity * _f(product.purchase_price), 2)

            if last is None:
                reason = (
                    f"Never sold, yet {product.stock_quantity} units in stock "
                    f"(Rs. {capital:,.0f} tied up). Consider a promotion or "
                    f"clearing it out."
                )
            else:
                reason = (
                    f"No sales in {days_since} days, {product.stock_quantity} units "
                    f"in stock (Rs. {capital:,.0f} tied up). Consider a discount to "
                    f"free up cash."
                )

            items.append(
                DeadStockItem(
                    product_id=product.id,
                    name=product.name,
                    sku=product.sku,
                    stock_quantity=product.stock_quantity,
                    days_since_last_sale=days_since,
                    capital_tied_up=capital,
                    reason=reason,
                )
            )

        # Most capital tied up first — that's what hurts cash flow most.
        items.sort(key=lambda d: d.capital_tied_up, reverse=True)
        return items

    # --- Frequently bought together -------------------------------------

    def frequently_bought_together(
        self, days: int, limit: int = 10, today: date | None = None
    ) -> FrequentlyBoughtTogether:
        """Product pairs that co-occur in the same sale (market-basket)."""
        today = today or date.today()
        window_sales = self._sales_in_window(days, today)
        total_sales = len(window_sales)

        if total_sales < MIN_SALES_FOR_FBT:
            return FrequentlyBoughtTogether(
                enough_data=False,
                total_sales=total_sales,
                min_sales_required=MIN_SALES_FOR_FBT,
                pairs=[],
            )

        pair_count: dict[tuple[int, int], int] = defaultdict(int)
        single_count: dict[int, int] = defaultdict(int)
        names: dict[int, str] = {}

        for sale in window_sales:
            # Distinct products in this basket.
            basket = {}
            for item in sale.items:
                basket[item.product_id] = item
            product_ids = sorted(basket)

            for pid in product_ids:
                single_count[pid] += 1
                if pid not in names and basket[pid].product is not None:
                    names[pid] = basket[pid].product.name

            for a, b in combinations(product_ids, 2):
                pair_count[(a, b)] += 1

        pairs: list[ProductPair] = []
        for (a, b), count in pair_count.items():
            pairs.append(
                ProductPair(
                    product_a_id=a,
                    product_a_name=names.get(a, f"#{a}"),
                    product_b_id=b,
                    product_b_name=names.get(b, f"#{b}"),
                    together_count=count,
                    support=round(count / total_sales, 4),
                    confidence_a_to_b=round(count / single_count[a], 4),
                    confidence_b_to_a=round(count / single_count[b], 4),
                )
            )

        pairs.sort(key=lambda p: p.together_count, reverse=True)
        return FrequentlyBoughtTogether(
            enough_data=True,
            total_sales=total_sales,
            min_sales_required=MIN_SALES_FOR_FBT,
            pairs=pairs[:limit],
        )
