"""Category CRUD routes."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_category_service, get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(
    service: CategoryService = Depends(get_category_service),
    _user: User = Depends(get_current_user),
) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in service.list()]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    _user: User = Depends(get_current_user),
) -> CategoryRead:
    return CategoryRead.model_validate(service.create(payload))


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    _user: User = Depends(get_current_user),
) -> CategoryRead:
    return CategoryRead.model_validate(service.get(category_id))


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    _user: User = Depends(get_current_user),
) -> CategoryRead:
    return CategoryRead.model_validate(service.update(category_id, payload))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    _user: User = Depends(get_current_user),
) -> None:
    service.delete(category_id)
