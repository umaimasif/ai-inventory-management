"""Regression: listing sales must not blow up on joined-eager-loaded items."""
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.services.sales_service import SalesService


def test_list_sales_with_multiple_items(db: Session) -> None:
    a = Product(name="A", sku="A-1", purchase_price=1, selling_price=2, stock_quantity=10)
    b = Product(name="B", sku="B-1", purchase_price=3, selling_price=5, stock_quantity=10)
    db.add_all([a, b])
    db.commit()

    service = SalesService(
        db, SaleRepository(db), ProductRepository(db), CustomerRepository(db)
    )
    service.create(
        SaleCreate(
            items=[
                SaleItemCreate(product_id=a.id, quantity=2),
                SaleItemCreate(product_id=b.id, quantity=1),
            ]
        )
    )

    # A joined eager load on Sale.items duplicates parent rows; without
    # .unique() this raises InvalidRequestError.
    listed = service.list()

    assert len(listed) == 1
    assert len(listed[0].items) == 2
