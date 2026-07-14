"""Customer ORM model."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Customer(Base, TimestampMixin, SoftDeleteMixin):
    """A customer. A single is_walkin default row lets anonymous sales count."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_walkin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
