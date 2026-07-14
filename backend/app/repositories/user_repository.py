"""Data-access layer for users. No business logic here."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Encapsulates all database queries for the User model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: int) -> User | None:
        """Return an active (non-deleted) user by id."""
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        return self._db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        """Return an active (non-deleted) user by email."""
        stmt = select(User).where(
            User.email == email, User.is_deleted.is_(False)
        )
        return self._db.scalar(stmt)

    def create(self, user: User) -> User:
        """Persist a new user and return it with its generated id."""
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
