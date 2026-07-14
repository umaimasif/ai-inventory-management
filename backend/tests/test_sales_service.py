"""Unit tests for the sales service — the core Phase 2 business logic."""
import pytest
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.services.errors import ValidationError
from app.services.sales_service import SalesService


def _service(db: Session) -> SalesService:
    return SalesService(
        db,
        SaleRepository(db),
        ProductRepository(db),
        CustomerRepository(db),
    )


def _product(db: Session, **kwargs) -> Product:
    defaults = dict(
        name="Widget",
        sku="W-1",
        purchase_price=10,
        selling_price=15,
        stock_quantity=100,
    )
    defaults.update(kwargs)
    product = Product(**defaults)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_sale_decrements_stock_and_computes_profit(db: Session) -> None:
    product = _product(db, stock_quantity=50, purchase_price=10, selling_price=15)
    service = _service(db)

    sale = service.create(
        SaleCreate(items=[SaleItemCreate(product_id=product.id, quantity=4)])
    )

    # Profit = (15 - 10) * 4 = 20; revenue = 15 * 4 = 60.
    assert float(sale.total_amount) == 60.0
    assert float(sale.total_profit) == 20.0
    assert len(sale.items) == 1

    db.refresh(product)
    assert product.stock_quantity == 46  # 50 - 4


def test_sale_without_customer_uses_walkin(db: Session) -> None:
    product = _product(db)
    service = _service(db)

    sale = service.create(
        SaleCreate(items=[SaleItemCreate(product_id=product.id, quantity=1)])
    )

    walkin = CustomerRepository(db).get_walkin()
    assert walkin is not None
    assert sale.customer_id == walkin.id


def test_sale_insufficient_stock_raises_and_leaves_stock_untouched(db: Session) -> None:
    product = _product(db, stock_quantity=3)
    service = _service(db)

    with pytest.raises(ValidationError):
        service.create(
            SaleCreate(items=[SaleItemCreate(product_id=product.id, quantity=5)])
        )

    db.refresh(product)
    assert product.stock_quantity == 3  # unchanged


def test_multi_item_sale_is_atomic_when_one_item_fails(db: Session) -> None:
    ok = _product(db, sku="OK", stock_quantity=10)
    short = _product(db, sku="SHORT", stock_quantity=1)
    service = _service(db)

    with pytest.raises(ValidationError):
        service.create(
            SaleCreate(
                items=[
                    SaleItemCreate(product_id=ok.id, quantity=2),
                    SaleItemCreate(product_id=short.id, quantity=5),
                ]
            )
        )

    # Neither product's stock should have changed.
    db.refresh(ok)
    db.refresh(short)
    assert ok.stock_quantity == 10
    assert short.stock_quantity == 1
    assert SaleRepository(db).count() == 0
