"""Generic repository with common CRUD operations.

Concrete repositories subclass this to avoid duplicating boilerplate.
All reads exclude soft-deleted rows.
"""
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD helpers shared by all repositories."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, entity_id: int) -> ModelT | None:
        """Return a non-deleted entity by id, or None."""
        entity = self._db.get(self.model, entity_id)
        if entity is None or getattr(entity, "is_deleted", False):
            return None
        return entity

    def list(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        """Return a page of non-deleted entities, newest first.

        `.unique()` is required because some models joined-eager-load a
        collection (e.g. Sale.items), which yields duplicate parent rows.
        """
        stmt = (
            select(self.model)
            .where(self.model.is_deleted.is_(False))
            .order_by(self.model.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).unique().all())

    def add(self, entity: ModelT) -> ModelT:
        """Persist a new entity."""
        self._db.add(entity)
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def save(self, entity: ModelT) -> ModelT:
        """Commit changes to an already-tracked entity."""
        self._db.commit()
        self._db.refresh(entity)
        return entity

    def soft_delete(self, entity: ModelT) -> None:
        """Mark an entity as deleted without removing the row."""
        entity.is_deleted = True
        self._db.commit()
