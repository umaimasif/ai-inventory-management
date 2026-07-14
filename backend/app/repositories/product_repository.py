"""Product data-access."""
from sqlalchemy import case, func, select

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    model = Product

    def get_by_sku(self, sku: str) -> Product | None:
        stmt = select(Product).where(
            Product.sku == sku, Product.is_deleted.is_(False)
        )
        return self._db.scalar(stmt)

    def list_low_stock(self) -> list[Product]:
        """Products whose stock is at or below their reorder threshold.

        Threshold is the greater of reorder_point and min_stock_level, so a
        product is flagged as soon as either bound is crossed.
        """
        # Portable "greatest of two columns" (SQLite lacks GREATEST, Postgres
        # lacks a two-arg MAX) via a CASE expression.
        threshold = case(
            (
                Product.reorder_point > Product.min_stock_level,
                Product.reorder_point,
            ),
            else_=Product.min_stock_level,
        )
        stmt = (
            select(Product)
            .where(
                Product.is_deleted.is_(False),
                Product.stock_quantity <= threshold,
            )
            .order_by(Product.stock_quantity.asc())
        )
        return list(self._db.scalars(stmt).all())

    def count(self) -> int:
        stmt = select(func.count(Product.id)).where(Product.is_deleted.is_(False))
        return self._db.scalar(stmt) or 0

    def count_out_of_stock(self) -> int:
        stmt = select(func.count(Product.id)).where(
            Product.is_deleted.is_(False), Product.stock_quantity <= 0
        )
        return self._db.scalar(stmt) or 0

    def total_stock_units(self) -> int:
        stmt = select(func.coalesce(func.sum(Product.stock_quantity), 0)).where(
            Product.is_deleted.is_(False)
        )
        return self._db.scalar(stmt) or 0
