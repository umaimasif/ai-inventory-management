"""Sales Analysis Agent — trends and best/worst sellers.

Single responsibility: interpret sales performance. It reads the analytics and
insights services; it does not touch stock levels or customers.
"""
from app.schemas.agents import AgentReport, Finding, Severity
from app.services.analytics_service import AnalyticsService
from app.services.insights_service import InsightsService

# Revenue swing (vs previous period) that is worth flagging.
NOTABLE_CHANGE_PCT = 15.0


class SalesAgent:
    name = "Sales Analysis Agent"

    def __init__(
        self, analytics: AnalyticsService, insights: InsightsService
    ) -> None:
        self._analytics = analytics
        self._insights = insights

    def run(self, days: int = 30) -> AgentReport:
        findings: list[Finding] = []

        kpis = self._analytics.kpis(days)
        change = kpis.revenue.change_pct

        if change is None:
            findings.append(
                Finding(
                    title="Not enough history to compare periods",
                    detail=f"Revenue in the last {days} days: Rs. "
                    f"{kpis.revenue.current:,.0f}.",
                    severity=Severity.info,
                )
            )
        elif change >= NOTABLE_CHANGE_PCT:
            findings.append(
                Finding(
                    title=f"Revenue up {change:.0f}% vs the previous {days} days",
                    detail=f"Rs. {kpis.revenue.previous:,.0f} → "
                    f"Rs. {kpis.revenue.current:,.0f}.",
                    severity=Severity.info,
                )
            )
        elif change <= -NOTABLE_CHANGE_PCT:
            findings.append(
                Finding(
                    title=f"Revenue down {abs(change):.0f}% vs the previous {days} days",
                    detail=f"Rs. {kpis.revenue.previous:,.0f} → "
                    f"Rs. {kpis.revenue.current:,.0f}. Worth investigating.",
                    severity=Severity.warning,
                )
            )

        top = self._analytics.top_products(days, limit=3)
        if top:
            names = ", ".join(f"{t.name} ({t.units_sold})" for t in top)
            findings.append(
                Finding(
                    title="Best sellers",
                    detail=f"Top by units: {names}.",
                    severity=Severity.info,
                )
            )

        worst = [w for w in self._insights.worst_sellers(days, limit=3) if w.units_sold == 0]
        if worst:
            names = ", ".join(w.name for w in worst)
            findings.append(
                Finding(
                    title=f"{len(worst)} product(s) with zero sales",
                    detail=f"No units sold in {days} days: {names}.",
                    severity=Severity.warning,
                )
            )

        if not findings:
            findings.append(
                Finding(
                    title="No notable sales signals",
                    detail="Sales are steady with no large swings.",
                    severity=Severity.info,
                )
            )

        return AgentReport(agent=self.name, findings=findings)
