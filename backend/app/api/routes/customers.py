"""Customer CRUD routes."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_customer_service
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerRead])
def list_customers(
    service: CustomerService = Depends(get_customer_service),
    _user: User = Depends(get_current_user),
) -> list[CustomerRead]:
    return [CustomerRead.model_validate(c) for c in service.list()]


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    _user: User = Depends(get_current_user),
) -> CustomerRead:
    return CustomerRead.model_validate(service.create(payload))


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
    _user: User = Depends(get_current_user),
) -> CustomerRead:
    return CustomerRead.model_validate(service.get(customer_id))


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
    _user: User = Depends(get_current_user),
) -> CustomerRead:
    return CustomerRead.model_validate(service.update(customer_id, payload))


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
    _user: User = Depends(get_current_user),
) -> None:
    service.delete(customer_id)
