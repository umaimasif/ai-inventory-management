"""Supplier CRUD routes."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_supplier_service
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services.supplier_service import SupplierService

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierRead])
def list_suppliers(
    service: SupplierService = Depends(get_supplier_service),
    _user: User = Depends(get_current_user),
) -> list[SupplierRead]:
    return [SupplierRead.model_validate(s) for s in service.list()]


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service),
    _user: User = Depends(get_current_user),
) -> SupplierRead:
    return SupplierRead.model_validate(service.create(payload))


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
    _user: User = Depends(get_current_user),
) -> SupplierRead:
    return SupplierRead.model_validate(service.get(supplier_id))


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service),
    _user: User = Depends(get_current_user),
) -> SupplierRead:
    return SupplierRead.model_validate(service.update(supplier_id, payload))


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service),
    _user: User = Depends(get_current_user),
) -> None:
    service.delete(supplier_id)
