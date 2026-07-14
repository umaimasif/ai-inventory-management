"""Stock audit data-access."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock_audit import StockAudit


class StockAuditRepository:
    """Stock audits are append-only; no soft delete or update."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, audit: StockAudit) -> StockAudit:
        self._db.add(audit)
        self._db.commit()
        self._db.refresh(audit)
        return audit

    def list(self, *, skip: int = 0, limit: int = 100) -> list[StockAudit]:
        stmt = (
            select(StockAudit)
            .order_by(StockAudit.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())
