"""Customer Intelligence Agent — segments customers by behavior.

Single responsibility: aggregate each customer's purchase history and assign a
segment (VIP / regular / new / inactive). The anonymous walk-in customer is
excluded — it aggregates unrelated sales and would distort every metric.

Segmentation rules (deterministic, explained per customer):
  - inactive : no purchase in the last INACTIVE_DAYS days (or never)
  - new      : signed up within NEW_DAYS days and few orders
  - vip      : total spend >= VIP_SPEND_MULTIPLE x the average spender
  - regular  : everyone else who has purchased
"""
from collections import defaultdict
from datetime import date

from app.repositories.customer_repository import CustomerRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.agents import (
    CustomerInsight,
    CustomerSegment,
    CustomerSegments,
)

INACTIVE_DAYS = 60
NEW_DAYS = 30
NEW_MAX_ORDERS = 2
VIP_SPEND_MULTIPLE = 1.5


def _f(value) -> float:
    return float(value or 0)


class _Agg:
    def __init__(self) -> None:
        self.total_spent = 0.0
        self.orders = 0
        self.last_purchase: date | None = None
        self.category_units: dict[str, int] = defaultdict(int)


class CustomerAgent:
    name = "Customer Intelligence Agent"

    def __init__(
        self, customers: CustomerRepository, sales: SaleRepository
    ) -> None:
        self._customers = customers
        self._sales = sales

    def run(self, today: date | None = None) -> CustomerSegments:
        today = today or date.today()

        # Aggregate all sales by customer.
        aggs: dict[int, _Agg] = defaultdict(_Agg)
        for sale in self._sales.list(limit=100000):
            if sale.customer_id is None:
                continue
            agg = aggs[sale.customer_id]
            agg.total_spent += _f(sale.total_amount)
            agg.orders += 1
            day = sale.created_at.date()
            if agg.last_purchase is None or day > agg.last_purchase:
                agg.last_purchase = day
            for item in sale.items:
                product = item.product
                category = getattr(product, "category", None) if product else None
                name = category.name if category else "Uncategorized"
                agg.category_units[name] += item.quantity

        # Average spend among customers who actually bought — the VIP baseline.
        spenders = [a.total_spent for a in aggs.values() if a.orders > 0]
        avg_spend = sum(spenders) / len(spenders) if spenders else 0.0

        insights: list[CustomerInsight] = []
        counts: dict[str, int] = defaultdict(int)

        for customer in self._customers.list(limit=100000):
            if customer.is_walkin:
                continue

            agg = aggs.get(customer.id, _Agg())
            days_since = (
                (today - agg.last_purchase).days
                if agg.last_purchase is not None
                else None
            )
            signed_up = customer.created_at.date()
            days_since_signup = (today - signed_up).days

            segment, reason = self._classify(
                agg, days_since, days_since_signup, avg_spend
            )

            favorite = (
                max(agg.category_units, key=agg.category_units.get)
                if agg.category_units
                else None
            )

            counts[segment.value] += 1
            insights.append(
                CustomerInsight(
                    customer_id=customer.id,
                    name=customer.name,
                    segment=segment,
                    total_spent=round(agg.total_spent, 2),
                    orders=agg.orders,
                    days_since_last_purchase=days_since,
                    favorite_category=favorite,
                    reason=reason,
                )
            )

        # Highest spenders first.
        insights.sort(key=lambda c: c.total_spent, reverse=True)
        return CustomerSegments(counts=dict(counts), customers=insights)

    @staticmethod
    def _classify(
        agg: _Agg,
        days_since: int | None,
        days_since_signup: int,
        avg_spend: float,
    ) -> tuple[CustomerSegment, str]:
        if agg.orders == 0 or days_since is None:
            return (
                CustomerSegment.inactive,
                "Has never made a purchase.",
            )

        if days_since > INACTIVE_DAYS:
            return (
                CustomerSegment.inactive,
                f"No purchase in {days_since} days. Consider a win-back offer.",
            )

        if days_since_signup <= NEW_DAYS and agg.orders <= NEW_MAX_ORDERS:
            return (
                CustomerSegment.new,
                f"Joined {days_since_signup} days ago with {agg.orders} order(s).",
            )

        if avg_spend > 0 and agg.total_spent >= avg_spend * VIP_SPEND_MULTIPLE:
            return (
                CustomerSegment.vip,
                f"Spent Rs. {agg.total_spent:,.0f} across {agg.orders} orders — "
                f"well above the Rs. {avg_spend:,.0f} average.",
            )

        return (
            CustomerSegment.regular,
            f"Spent Rs. {agg.total_spent:,.0f} across {agg.orders} orders.",
        )
