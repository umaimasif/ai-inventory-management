"""Product CRUD + stock adjustment routes."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_product_service
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    StockAdjust,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> list[ProductRead]:
    return [ProductRead.model_validate(p) for p in service.list()]


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> ProductRead:
    return ProductRead.model_validate(service.create(payload))


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> ProductRead:
    return ProductRead.model_validate(service.get(product_id))


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> ProductRead:
    return ProductRead.model_validate(service.update(product_id, payload))


@router.post("/{product_id}/adjust-stock", response_model=ProductRead)
def adjust_stock(
    product_id: int,
    payload: StockAdjust,
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> ProductRead:
    return ProductRead.model_validate(service.adjust_stock(product_id, payload.delta))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    _user: User = Depends(get_current_user),
) -> None:
    service.delete(product_id)
