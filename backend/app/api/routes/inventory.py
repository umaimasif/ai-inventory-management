"""Inventory oversight routes: dashboard summary, low-stock, stock audits."""
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_inventory_service
from app.models.user import User
from app.schemas.inventory import (
    DashboardSummary,
    LowStockItem,
    StockAuditCreate,
    StockAuditRead,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    service: InventoryService = Depends(get_inventory_service),
    _user: User = Depends(get_current_user),
) -> DashboardSummary:
    return service.summary()


@router.get("/low-stock", response_model=list[LowStockItem])
def low_stock(
    service: InventoryService = Depends(get_inventory_service),
    _user: User = Depends(get_current_user),
) -> list[LowStockItem]:
    return service.low_stock()


@router.get("/audits", response_model=list[StockAuditRead])
def list_audits(
    service: InventoryService = Depends(get_inventory_service),
    _user: User = Depends(get_current_user),
) -> list[StockAuditRead]:
    return [StockAuditRead.model_validate(a) for a in service.list_audits()]


@router.post(
    "/audits", response_model=StockAuditRead, status_code=status.HTTP_201_CREATED
)
def record_audit(
    payload: StockAuditCreate,
    service: InventoryService = Depends(get_inventory_service),
    _user: User = Depends(get_current_user),
) -> StockAuditRead:
    return StockAuditRead.model_validate(service.record_audit(payload))
