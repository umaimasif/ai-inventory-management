"""Sale and SaleItem ORM models."""
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Sale(Base, TimestampMixin, SoftDeleteMixin):
    """A single sale transaction, made up of one or more line items."""

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"), nullable=True, index=True
    )
    payment_method: Mapped[str] = mapped_column(String(30), default="cash", nullable=False)

    # Denormalized totals, computed at sale time.
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total_profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class SaleItem(Base, TimestampMixin):
    """A line item within a sale. Captures price/cost at time of sale."""

    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    line_profit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["object"] = relationship("Product", lazy="joined")
