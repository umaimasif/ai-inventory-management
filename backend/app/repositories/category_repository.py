"""Category data-access."""
from sqlalchemy import select

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(
            Category.name == name, Category.is_deleted.is_(False)
        )
        return self._db.scalar(stmt)
