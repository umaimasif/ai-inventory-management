"""Product ORM model."""
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Product(Base, TimestampMixin, SoftDeleteMixin):
    """A sellable product with stock and pricing."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"), nullable=True, index=True
    )

    # Pricing stored as Numeric to avoid float rounding on money.
    purchase_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    selling_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    # Stock levels.
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped["object"] = relationship("Category", lazy="joined")
    supplier: Mapped["object"] = relationship("Supplier", lazy="joined")
