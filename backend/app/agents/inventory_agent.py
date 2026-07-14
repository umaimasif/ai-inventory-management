"""Inventory Agent — monitors stock health.

Single responsibility: surface stock problems (low, out, dead, overstock).
It reads only from the inventory and insights services; it does not analyze
sales trends or customers (those are other agents' jobs).
"""
from app.repositories.product_repository import ProductRepository
from app.schemas.agents import AgentReport, Finding, Severity
from app.services.insights_service import InsightsService
from app.services.inventory_service import InventoryService

# A product is "overstocked" when it holds far more than its reorder point.
OVERSTOCK_MULTIPLE = 5


class InventoryAgent:
    name = "Inventory Agent"

    def __init__(
        self,
        inventory: InventoryService,
        insights: InsightsService,
        products: ProductRepository,
    ) -> None:
        self._inventory = inventory
        self._insights = insights
        self._products = products

    def run(self) -> AgentReport:
        findings: list[Finding] = []

        summary = self._inventory.summary()

        if summary.out_of_stock_count:
            findings.append(
                Finding(
                    title=f"{summary.out_of_stock_count} product(s) out of stock",
                    detail="These cannot be sold until restocked.",
                    severity=Severity.critical,
                )
            )

        low = self._inventory.low_stock()
        if low:
            names = ", ".join(item.product.name for item in low[:5])
            findings.append(
                Finding(
                    title=f"{len(low)} product(s) at or below reorder point",
                    detail=f"Reorder soon: {names}"
                    + ("…" if len(low) > 5 else ""),
                    severity=Severity.warning,
                )
            )

        dead = self._insights.dead_stock(days=30)
        if dead:
            capital = sum(d.capital_tied_up for d in dead)
            findings.append(
                Finding(
                    title=f"{len(dead)} dead-stock item(s), Rs. {capital:,.0f} tied up",
                    detail="No recent sales — consider discounts or clearance.",
                    severity=Severity.warning,
                )
            )

        overstocked = [
            p
            for p in self._products.list(limit=100000)
            if p.reorder_point > 0
            and p.stock_quantity >= p.reorder_point * OVERSTOCK_MULTIPLE
        ]
        if overstocked:
            names = ", ".join(p.name for p in overstocked[:5])
            findings.append(
                Finding(
                    title=f"{len(overstocked)} product(s) overstocked",
                    detail=f"Holding well above reorder point: {names}"
                    + ("…" if len(overstocked) > 5 else ""),
                    severity=Severity.info,
                )
            )

        if not findings:
            findings.append(
                Finding(
                    title="Inventory healthy",
                    detail="No stock issues detected.",
                    severity=Severity.info,
                )
            )

        return AgentReport(agent=self.name, findings=findings)
