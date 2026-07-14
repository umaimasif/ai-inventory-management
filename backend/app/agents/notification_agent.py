"""Notification Agent — the morning report and smart alerts.

Single responsibility: communication. It assembles facts from the other agents
and services into a daily summary, and raises urgent alerts. The narrative is
phrased by the LLM when configured, otherwise by a deterministic template — the
underlying facts are identical either way (grounding).
"""
from datetime import date

from app.agents.recommendation_agent import RecommendationAgent
from app.core.llm import phrase
from app.schemas.agents import Alert, MorningReport, Severity
from app.services.analytics_service import AnalyticsService
from app.services.forecast_service import ForecastService
from app.services.inventory_service import InventoryService

# Days-of-stock at/below which stock is critically low.
CRITICAL_DAYS_LEFT = 2
# Revenue drop (%) vs the previous period that warrants an alert.
SALES_DROP_ALERT_PCT = -20.0


class NotificationAgent:
    name = "Notification Agent"

    def __init__(
        self,
        analytics: AnalyticsService,
        inventory: InventoryService,
        forecast: ForecastService,
        recommendations: RecommendationAgent,
    ) -> None:
        self._analytics = analytics
        self._inventory = inventory
        self._forecast = forecast
        self._recommendations = recommendations

    # --- Alerts ---------------------------------------------------------

    def alerts(self, days: int = 30, today: date | None = None) -> list[Alert]:
        alerts: list[Alert] = []

        summary = self._inventory.summary()
        if summary.out_of_stock_count:
            alerts.append(
                Alert(
                    title=f"{summary.out_of_stock_count} product(s) out of stock",
                    detail="Restock immediately — these are unsellable.",
                    severity=Severity.critical,
                )
            )

        for f in self._forecast.forecast(days, today):
            if (
                f.days_of_stock_left is not None
                and f.days_of_stock_left <= CRITICAL_DAYS_LEFT
            ):
                alerts.append(
                    Alert(
                        title=f"{f.name} runs out in ~{f.days_of_stock_left:.0f} day(s)",
                        detail=f"Selling ~{f.avg_daily_demand:.1f}/day with "
                        f"{f.stock_quantity} left. Reorder {f.recommended_reorder_qty}.",
                        severity=Severity.critical,
                    )
                )

        change = self._analytics.kpis(days, today).revenue.change_pct
        if change is not None and change <= SALES_DROP_ALERT_PCT:
            alerts.append(
                Alert(
                    title=f"Revenue down {abs(change):.0f}% vs the previous period",
                    detail="A significant drop — worth investigating today.",
                    severity=Severity.warning,
                )
            )

        return alerts

    # --- Morning report -------------------------------------------------

    def morning_report(self, day: date | None = None) -> MorningReport:
        report = self._analytics.daily_report(day)
        recs = self._recommendations.run(days=30, today=day)
        alerts = self.alerts(days=30, today=day)

        # Facts handed to the LLM — the ONLY information it may use.
        facts = {
            "date": str(report.day),
            "revenue": report.revenue,
            "profit": report.profit,
            "orders": report.orders,
            "units_sold": report.units_sold,
            "best_sellers": [
                {"name": p.name, "units": p.units_sold} for p in report.top_products
            ],
            "low_stock_count": report.low_stock_count,
            "out_of_stock_count": report.out_of_stock_count,
            "top_recommendations": [
                {"title": r.title, "reason": r.reason} for r in recs[:5]
            ],
            "alerts": [{"title": a.title} for a in alerts],
        }

        narrative = phrase(
            "Write a short 'Good morning' business summary for the store manager.",
            facts,
        )
        llm_used = narrative is not None
        if narrative is None:
            narrative = self._template_narrative(report, recs, alerts)

        return MorningReport(
            report=report,
            recommendations=recs[:8],
            alerts=alerts,
            narrative=narrative,
            llm_used=llm_used,
        )

    @staticmethod
    def _template_narrative(report, recs, alerts) -> str:
        """Deterministic fallback wording — used when no LLM is configured."""
        lines = [
            "Good morning!",
            "",
            f"Yesterday ({report.day}):",
            f"  Revenue: Rs. {report.revenue:,.0f}",
            f"  Profit:  Rs. {report.profit:,.0f}",
            f"  Orders:  {report.orders}",
        ]

        if report.top_products:
            best = ", ".join(f"{p.name} ({p.units_sold})" for p in report.top_products[:3])
            lines += ["", f"Best sellers: {best}"]

        restocks = [r for r in recs if r.category == "restock"][:5]
        if restocks:
            lines += ["", "Restock soon:"]
            lines += [f"  • {r.title}" for r in restocks]

        clear = [r for r in recs if r.category == "clearance"][:3]
        if clear:
            lines += ["", "Consider clearing:"]
            lines += [f"  • {r.title}" for r in clear]

        bundles = [r for r in recs if r.category == "bundle"][:3]
        if bundles:
            lines += ["", "Bundle ideas:"]
            lines += [f"  • {r.title}" for r in bundles]

        if alerts:
            lines += ["", "Alerts:"]
            lines += [f"  ⚠ {a.title}" for a in alerts]

        return "\n".join(lines)
