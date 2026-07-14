"""Manager Assistant Agent — grounded natural-language Q&A.

Single responsibility: answer the manager's questions using real business data.

Grounding is enforced structurally, not by trusting the model:
  1. The question is classified into an INTENT by keyword rules.
  2. The intent runs a deterministic query and produces a FACTS object.
  3. A template answer is written from those facts.
  4. If an LLM is configured, it is asked to phrase the SAME facts — it never
     sees the database and is told to use only the provided facts. If it fails
     or is absent, the template answer is used.

So the numbers a manager sees always come from a real query, never from the
model's imagination. The exact facts are returned in `grounded_on`.
"""
from datetime import date

from app.agents.customer_agent import CustomerAgent
from app.core.llm import phrase
from app.schemas.agents import ChatResponse
from app.schemas.agents import CustomerSegment
from app.services.analytics_service import AnalyticsService
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService

WINDOW_DAYS = 30


class ManagerAssistant:
    name = "Manager Assistant"

    def __init__(
        self,
        analytics: AnalyticsService,
        insights: InsightsService,
        forecast: ForecastService,
        customers: CustomerAgent,
    ) -> None:
        self._analytics = analytics
        self._insights = insights
        self._forecast = forecast
        self._customers = customers

    def ask(self, question: str, today: date | None = None) -> ChatResponse:
        today = today or date.today()
        intent = self._classify(question)
        facts, template = self._answer_for_intent(intent, today)

        narrative = phrase(
            f"Answer the manager's question: '{question}'", facts
        )
        llm_used = narrative is not None
        answer = narrative if narrative is not None else template

        return ChatResponse(
            answer=answer,
            intent=intent,
            grounded_on=facts,
            llm_used=llm_used,
        )

    # --- Intent classification -----------------------------------------

    @staticmethod
    def _classify(question: str) -> str:
        q = question.lower()

        def has(*words: str) -> bool:
            return any(w in q for w in words)

        if has("order", "reorder", "restock", "buy", "purchase"):
            return "restock"
        if has("discount", "clear", "dead stock", "promote", "get rid"):
            return "clearance"
        if has("bought together", "bundle", "combo", "frequently"):
            return "bundle"
        if has("customer", "loyal", "vip", "spend the most", "spender"):
            return "top_customers"
        if has("expected revenue", "next week", "forecast revenue", "predict revenue"):
            return "revenue_forecast"
        if has("why", "decreas", "down", "drop", "fall", "declin"):
            return "sales_trend"
        if has("sold the most", "best seller", "top product", "most this"):
            return "top_products"
        return "summary"

    # --- Grounded answers per intent -----------------------------------

    def _answer_for_intent(self, intent: str, today: date) -> tuple[dict, str]:
        handler = {
            "restock": self._restock,
            "clearance": self._clearance,
            "bundle": self._bundle,
            "top_customers": self._top_customers,
            "revenue_forecast": self._revenue_forecast,
            "sales_trend": self._sales_trend,
            "top_products": self._top_products,
            "summary": self._summary,
        }[intent]
        return handler(today)

    def _restock(self, today: date) -> tuple[dict, str]:
        forecasts = [
            f for f in self._forecast.forecast(WINDOW_DAYS, today)
            if f.recommended_reorder_qty > 0
        ]
        facts = {
            "products_to_reorder": [
                {
                    "name": f.name,
                    "reorder_qty": f.recommended_reorder_qty,
                    "days_of_stock_left": f.days_of_stock_left,
                    "confidence": f.confidence.value,
                }
                for f in forecasts[:10]
            ]
        }
        if not forecasts:
            return facts, "Nothing needs reordering right now — stock levels look healthy."
        lines = ["Based on current demand, reorder these:"]
        lines += [
            f"  • {f.name}: {f.recommended_reorder_qty} units "
            f"(~{f.days_of_stock_left:.0f} days left, {f.confidence.value} confidence)"
            for f in forecasts[:10]
        ]
        return facts, "\n".join(lines)

    def _clearance(self, today: date) -> tuple[dict, str]:
        dead = self._insights.dead_stock(days=30, today=today)
        facts = {
            "dead_stock": [
                {"name": d.name, "capital_tied_up": d.capital_tied_up, "reason": d.reason}
                for d in dead[:10]
            ]
        }
        if not dead:
            return facts, "No dead stock to clear — everything is selling."
        lines = ["Consider discounting or clearing these — cash is tied up:"]
        lines += [f"  • {d.name}: Rs. {d.capital_tied_up:,.0f} tied up" for d in dead[:10]]
        return facts, "\n".join(lines)

    def _bundle(self, today: date) -> tuple[dict, str]:
        fbt = self._insights.frequently_bought_together(WINDOW_DAYS, limit=5, today=today)
        facts = {
            "enough_data": fbt.enough_data,
            "pairs": [
                {
                    "a": p.product_a_name,
                    "b": p.product_b_name,
                    "together_count": p.together_count,
                    "support_pct": round(p.support * 100),
                }
                for p in fbt.pairs
            ],
        }
        if not fbt.enough_data:
            return facts, (
                f"Not enough sales yet to find reliable pairings "
                f"({fbt.total_sales} of {fbt.min_sales_required} needed)."
            )
        if not fbt.pairs:
            return facts, "No strong product pairings found yet."
        lines = ["These are often bought together — good bundle candidates:"]
        lines += [
            f"  • {p.product_a_name} + {p.product_b_name} "
            f"({p.together_count} times)"
            for p in fbt.pairs
        ]
        return facts, "\n".join(lines)

    def _top_customers(self, today: date) -> tuple[dict, str]:
        segments = self._customers.run(today)
        vips = [c for c in segments.customers if c.segment == CustomerSegment.vip]
        top = sorted(segments.customers, key=lambda c: c.total_spent, reverse=True)[:5]
        facts = {
            "segment_counts": segments.counts,
            "top_spenders": [
                {"name": c.name, "total_spent": c.total_spent, "orders": c.orders}
                for c in top
            ],
            "vip_count": len(vips),
        }
        if not top or top[0].total_spent == 0:
            return facts, "No customer purchase history yet."
        lines = ["Your top customers by spending:"]
        lines += [
            f"  • {c.name}: Rs. {c.total_spent:,.0f} across {c.orders} orders"
            for c in top
        ]
        return facts, "\n".join(lines)

    def _revenue_forecast(self, today: date) -> tuple[dict, str]:
        series = self._analytics.daily_series(WINDOW_DAYS, today)
        avg_daily = (
            sum(p.revenue for p in series) / len(series) if series else 0.0
        )
        next_week = round(avg_daily * 7, 2)
        facts = {
            "avg_daily_revenue": round(avg_daily, 2),
            "projected_next_7_days": next_week,
            "method": "average daily revenue over the last 30 days × 7",
            "confidence": "low" if len(series) < 14 else "medium",
        }
        return facts, (
            f"Estimated revenue for the next 7 days: Rs. {next_week:,.0f} "
            f"(based on the last 30 days' average of Rs. {avg_daily:,.0f}/day). "
            f"This is a simple projection, not a guarantee."
        )

    def _sales_trend(self, today: date) -> tuple[dict, str]:
        kpis = self._analytics.kpis(WINDOW_DAYS, today)
        change = kpis.revenue.change_pct
        facts = {
            "current_revenue": kpis.revenue.current,
            "previous_revenue": kpis.revenue.previous,
            "change_pct": change,
            "orders_current": kpis.orders.current,
            "orders_previous": kpis.orders.previous,
        }
        if change is None:
            return facts, (
                f"There isn't a full previous period to compare against yet. "
                f"Revenue over the last {WINDOW_DAYS} days was "
                f"Rs. {kpis.revenue.current:,.0f}."
            )
        direction = "up" if change >= 0 else "down"
        return facts, (
            f"Revenue is {direction} {abs(change):.0f}% vs the previous "
            f"{WINDOW_DAYS} days (Rs. {kpis.revenue.previous:,.0f} → "
            f"Rs. {kpis.revenue.current:,.0f}). Orders went from "
            f"{kpis.orders.previous:.0f} to {kpis.orders.current:.0f}."
        )

    def _top_products(self, today: date) -> tuple[dict, str]:
        top = self._analytics.top_products(WINDOW_DAYS, limit=5, today=today)
        facts = {
            "top_products": [
                {"name": t.name, "units_sold": t.units_sold, "revenue": t.revenue}
                for t in top
            ]
        }
        if not top:
            return facts, "No sales recorded in this period yet."
        lines = [f"Best sellers over the last {WINDOW_DAYS} days:"]
        lines += [f"  • {t.name}: {t.units_sold} units (Rs. {t.revenue:,.0f})" for t in top]
        return facts, "\n".join(lines)

    def _summary(self, today: date) -> tuple[dict, str]:
        kpis = self._analytics.kpis(WINDOW_DAYS, today)
        facts = {
            "window_days": WINDOW_DAYS,
            "revenue": kpis.revenue.current,
            "profit": kpis.profit.current,
            "orders": kpis.orders.current,
            "units_sold": kpis.units_sold.current,
        }
        return facts, (
            f"Over the last {WINDOW_DAYS} days: Rs. {kpis.revenue.current:,.0f} "
            f"revenue, Rs. {kpis.profit.current:,.0f} profit, "
            f"{kpis.orders.current:.0f} orders. Ask me about restocking, slow "
            f"movers, best sellers, or your top customers."
        )
