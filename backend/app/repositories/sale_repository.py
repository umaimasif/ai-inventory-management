"""Sale data-access."""
from datetime import datetime

from sqlalchemy import func, select

from app.models.sale import Sale
from app.repositories.base import BaseRepository


class SaleRepository(BaseRepository[Sale]):
    model = Sale

    def count(self) -> int:
        stmt = select(func.count(Sale.id)).where(Sale.is_deleted.is_(False))
        return self._db.scalar(stmt) or 0

    def list_between(self, start: datetime, end: datetime) -> list[Sale]:
        """Sales created in [start, end). Items are eager-loaded on the model."""
        stmt = (
            select(Sale)
            .where(
                Sale.is_deleted.is_(False),
                Sale.created_at >= start,
                Sale.created_at < end,
            )
            .order_by(Sale.created_at.asc())
        )
        return list(self._db.scalars(stmt).unique().all())
