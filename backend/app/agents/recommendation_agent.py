"""Recommendation Agent — the synthesizer.

Single responsibility: combine the outputs of the forecast and insights layers
into a prioritized, actionable list. Every recommendation states WHY, per the
design rule that the AI must explain its reasoning, never just show data.
"""
from datetime import date

from app.schemas.agents import Priority, Recommendation
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService

# How many bundle suggestions to surface from market-basket analysis.
MAX_BUNDLES = 3
# Days-of-stock at/below which a reorder becomes high priority.
URGENT_DAYS_LEFT = 3


class RecommendationAgent:
    name = "Recommendation Agent"

    def __init__(
        self, forecast: ForecastService, insights: InsightsService
    ) -> None:
        self._forecast = forecast
        self._insights = insights

    def run(self, days: int = 30, today: date | None = None) -> list[Recommendation]:
        recs: list[Recommendation] = []

        # 1. Restock, from the forecast.
        for f in self._forecast.forecast(days, today):
            if f.recommended_reorder_qty <= 0:
                continue
            urgent = f.days_of_stock_left is not None and f.days_of_stock_left <= URGENT_DAYS_LEFT
            recs.append(
                Recommendation(
                    title=f"Reorder {f.recommended_reorder_qty} units of {f.name}",
                    reason=f.reason,
                    priority=Priority.high if urgent else Priority.medium,
                    category="restock",
                )
            )

        # 2. Clear dead stock (also implicitly "do not reorder").
        for d in self._insights.dead_stock(days=30, today=today):
            recs.append(
                Recommendation(
                    title=f"Discount or clear {d.name}",
                    reason=d.reason,
                    priority=Priority.medium if d.capital_tied_up >= 5000 else Priority.low,
                    category="clearance",
                )
            )

        # 3. Bundle opportunities, from market-basket analysis.
        fbt = self._insights.frequently_bought_together(days, limit=MAX_BUNDLES, today=today)
        if fbt.enough_data:
            for pair in fbt.pairs:
                recs.append(
                    Recommendation(
                        title=f"Bundle {pair.product_a_name} + {pair.product_b_name}",
                        reason=(
                            f"Bought together {pair.together_count} times "
                            f"({round(pair.support * 100)}% of sales). A combo offer "
                            f"or shelf placement could lift both."
                        ),
                        priority=Priority.low,
                        category="bundle",
                    )
                )

        # Highest priority first.
        order = {Priority.high: 0, Priority.medium: 1, Priority.low: 2}
        recs.sort(key=lambda r: order[r.priority])
        return recs
