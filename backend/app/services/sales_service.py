"""Sales business logic: records a sale, decrements stock, computes profit.

All work happens in one transaction. Items are fully validated before any
stock is touched, so a failure part-way leaves nothing half-applied.
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.sale import Sale, SaleItem
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate
from app.services.errors import NotFoundError, ValidationError


class SalesService:
    def __init__(
        self,
        db: Session,
        sales: SaleRepository,
        products: ProductRepository,
        customers: CustomerRepository,
    ) -> None:
        self._db = db
        self._sales = sales
        self._products = products
        self._customers = customers

    def list(self) -> list[Sale]:
        return self._sales.list(limit=200)

    def get(self, sale_id: int) -> Sale:
        sale = self._sales.get(sale_id)
        if sale is None:
            raise NotFoundError("Sale not found")
        return sale

    def create(self, data: SaleCreate) -> Sale:
        # Resolve the customer: explicit id, or fall back to the walk-in row.
        if data.customer_id is not None:
            customer = self._customers.get(data.customer_id)
            if customer is None:
                raise ValidationError("Referenced customer does not exist")
            customer_id = customer.id
        else:
            customer_id = self._customers.get_or_create_walkin().id

        # Pass 1: validate every line and gather the products. No mutation yet.
        planned: list[tuple] = []
        for item in data.items:
            product = self._products.get(item.product_id)
            if product is None:
                raise ValidationError(f"Product {item.product_id} does not exist")
            if item.quantity > product.stock_quantity:
                raise ValidationError(
                    f"Insufficient stock for '{product.name}': "
                    f"requested {item.quantity}, available {product.stock_quantity}"
                )
            planned.append((product, item.quantity))

        # Pass 2: build the sale, decrement stock, accumulate totals.
        sale = Sale(customer_id=customer_id, payment_method=data.payment_method)
        total_amount = Decimal("0")
        total_profit = Decimal("0")

        for product, quantity in planned:
            unit_price = Decimal(str(product.selling_price))
            unit_cost = Decimal(str(product.purchase_price))
            line_total = unit_price * quantity
            line_profit = (unit_price - unit_cost) * quantity

            sale.items.append(
                SaleItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    line_total=line_total,
                    line_profit=line_profit,
                )
            )
            product.stock_quantity -= quantity
            total_amount += line_total
            total_profit += line_profit

        sale.total_amount = total_amount
        sale.total_profit = total_profit

        # Single commit persists the sale, its items, and the stock changes.
        return self._sales.add(sale)
