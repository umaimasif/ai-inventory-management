"""StockAudit ORM model — records physical counts vs system counts."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class StockAudit(Base, TimestampMixin):
    """A stock count event. difference < 0 signals possible inventory loss."""

    __tablename__ = "stock_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    system_count: Mapped[int] = mapped_column(Integer, nullable=False)
    physical_count: Mapped[int] = mapped_column(Integer, nullable=False)
    difference: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    product: Mapped["object"] = relationship("Product", lazy="joined")
