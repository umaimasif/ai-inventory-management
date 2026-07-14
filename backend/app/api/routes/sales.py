"""Sales routes."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_sales_service
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleRead
from app.services.sales_service import SalesService

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=list[SaleRead])
def list_sales(
    service: SalesService = Depends(get_sales_service),
    _user: User = Depends(get_current_user),
) -> list[SaleRead]:
    return [SaleRead.model_validate(s) for s in service.list()]


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    service: SalesService = Depends(get_sales_service),
    _user: User = Depends(get_current_user),
) -> SaleRead:
    return SaleRead.model_validate(service.create(payload))


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale(
    sale_id: int,
    service: SalesService = Depends(get_sales_service),
    _user: User = Depends(get_current_user),
) -> SaleRead:
    return SaleRead.model_validate(service.get(sale_id))
