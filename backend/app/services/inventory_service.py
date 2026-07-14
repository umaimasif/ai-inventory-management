"""Inventory oversight: low-stock report, stock audits, dashboard KPIs."""
from app.models.stock_audit import StockAudit
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.stock_audit_repository import StockAuditRepository
from app.schemas.inventory import (
    DashboardSummary,
    LowStockItem,
    StockAuditCreate,
)
from app.services.errors import NotFoundError


class InventoryService:
    def __init__(
        self,
        products: ProductRepository,
        customers: CustomerRepository,
        sales: SaleRepository,
        audits: StockAuditRepository,
    ) -> None:
        self._products = products
        self._customers = customers
        self._sales = sales
        self._audits = audits

    def low_stock(self) -> list[LowStockItem]:
        """Products at/below their reorder threshold, with the shortfall."""
        items: list[LowStockItem] = []
        for product in self._products.list_low_stock():
            threshold = max(product.reorder_point, product.min_stock_level)
            items.append(
                LowStockItem(
                    product=product,  # type: ignore[arg-type]
                    shortfall=max(threshold - product.stock_quantity, 0),
                )
            )
        return items

    def summary(self) -> DashboardSummary:
        """KPI counts for the dashboard."""
        return DashboardSummary(
            total_products=self._products.count(),
            low_stock_count=len(self._products.list_low_stock()),
            out_of_stock_count=self._products.count_out_of_stock(),
            total_stock_units=self._products.total_stock_units(),
            total_customers=len(self._customers.list(limit=100000)),
            total_sales=self._sales.count(),
        )

    def record_audit(self, data: StockAuditCreate) -> StockAudit:
        """Record a physical count and reconcile system stock to match it.

        difference = physical - system. A negative difference flags possible
        inventory loss / shrinkage.
        """
        product = self._products.get(data.product_id)
        if product is None:
            raise NotFoundError("Product not found")

        system_count = product.stock_quantity
        difference = data.physical_count - system_count

        audit = StockAudit(
            product_id=product.id,
            system_count=system_count,
            physical_count=data.physical_count,
            difference=difference,
            note=data.note,
        )
        # Reconcile system stock to the physical reality.
        product.stock_quantity = data.physical_count
        return self._audits.add(audit)

    def list_audits(self) -> list[StockAudit]:
        return self._audits.list(limit=200)
