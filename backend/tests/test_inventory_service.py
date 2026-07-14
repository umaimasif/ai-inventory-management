"""Unit tests for inventory oversight: low-stock, audits, KPI summary."""
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.stock_audit_repository import StockAuditRepository
from app.schemas.inventory import StockAuditCreate
from app.services.inventory_service import InventoryService


def _service(db: Session) -> InventoryService:
    return InventoryService(
        ProductRepository(db),
        CustomerRepository(db),
        SaleRepository(db),
        StockAuditRepository(db),
    )


def _product(db: Session, **kwargs) -> Product:
    defaults = dict(name="P", sku="P-1", stock_quantity=0)
    defaults.update(kwargs)
    product = Product(**defaults)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_low_stock_flags_products_at_or_below_threshold(db: Session) -> None:
    _product(db, sku="LOW", stock_quantity=2, reorder_point=5, min_stock_level=3)
    _product(db, sku="OK", stock_quantity=20, reorder_point=5, min_stock_level=3)
    service = _service(db)

    low = service.low_stock()

    assert len(low) == 1
    assert low[0].product.sku == "LOW"
    # threshold = max(5, 3) = 5; shortfall = 5 - 2 = 3.
    assert low[0].shortfall == 3


def test_audit_records_difference_and_reconciles_stock(db: Session) -> None:
    product = _product(db, stock_quantity=10)
    service = _service(db)

    audit = service.record_audit(
        StockAuditCreate(product_id=product.id, physical_count=7, note="shrinkage")
    )

    assert audit.system_count == 10
    assert audit.physical_count == 7
    assert audit.difference == -3  # negative → possible loss

    db.refresh(product)
    assert product.stock_quantity == 7  # reconciled to physical count


def test_summary_counts(db: Session) -> None:
    _product(db, sku="A", stock_quantity=0, reorder_point=5)  # out of stock + low
    _product(db, sku="B", stock_quantity=50)
    service = _service(db)

    summary = service.summary()

    assert summary.total_products == 2
    assert summary.out_of_stock_count == 1
    assert summary.low_stock_count == 1
    assert summary.total_stock_units == 50
