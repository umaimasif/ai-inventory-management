"""Category business logic."""
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.errors import ConflictError, NotFoundError


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def list(self) -> list[Category]:
        return self._repo.list(limit=500)

    def get(self, category_id: int) -> Category:
        category = self._repo.get(category_id)
        if category is None:
            raise NotFoundError("Category not found")
        return category

    def create(self, data: CategoryCreate) -> Category:
        if self._repo.get_by_name(data.name):
            raise ConflictError("A category with that name already exists")
        return self._repo.add(Category(**data.model_dump()))

    def update(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get(category_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            existing = self._repo.get_by_name(changes["name"])
            if existing and existing.id != category_id:
                raise ConflictError("A category with that name already exists")
        for field, value in changes.items():
            setattr(category, field, value)
        return self._repo.save(category)

    def delete(self, category_id: int) -> None:
        self._repo.soft_delete(self.get(category_id))
