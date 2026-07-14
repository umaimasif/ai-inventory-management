"""Insight + forecast routes (Phase 4)."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_current_user,
    get_forecast_service,
    get_insights_service,
)
from app.models.user import User
from app.schemas.insights import (
    DeadStockItem,
    FrequentlyBoughtTogether,
    ProductForecast,
    WorstSeller,
)
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["insights"])

DaysQuery = Query(default=30, ge=1, le=365, description="Window size in days")


@router.get("/worst-sellers", response_model=list[WorstSeller])
def worst_sellers(
    days: int = DaysQuery,
    limit: int = Query(default=10, ge=1, le=50),
    service: InsightsService = Depends(get_insights_service),
    _user: User = Depends(get_current_user),
) -> list[WorstSeller]:
    return service.worst_sellers(days, limit)


@router.get("/dead-stock", response_model=list[DeadStockItem])
def dead_stock(
    days: int = DaysQuery,
    service: InsightsService = Depends(get_insights_service),
    _user: User = Depends(get_current_user),
) -> list[DeadStockItem]:
    return service.dead_stock(days)


@router.get("/frequently-bought-together", response_model=FrequentlyBoughtTogether)
def frequently_bought_together(
    days: int = DaysQuery,
    limit: int = Query(default=10, ge=1, le=50),
    service: InsightsService = Depends(get_insights_service),
    _user: User = Depends(get_current_user),
) -> FrequentlyBoughtTogether:
    return service.frequently_bought_together(days, limit)


@router.get("/forecast", response_model=list[ProductForecast])
def forecast(
    days: int = DaysQuery,
    service: ForecastService = Depends(get_forecast_service),
    _user: User = Depends(get_current_user),
) -> list[ProductForecast]:
    return service.forecast(days)
