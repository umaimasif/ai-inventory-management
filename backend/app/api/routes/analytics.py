"""Analytics + reporting routes."""
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service, get_current_user
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsKpis,
    DailyPoint,
    DailyReport,
    PaymentSlice,
    TopCategory,
    TopProduct,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Shared window parameter: how many days back to analyze.
DaysQuery = Query(default=30, ge=1, le=365, description="Window size in days")


@router.get("/kpis", response_model=AnalyticsKpis)
def kpis(
    days: int = DaysQuery,
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> AnalyticsKpis:
    return service.kpis(days)


@router.get("/daily", response_model=list[DailyPoint])
def daily_series(
    days: int = DaysQuery,
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> list[DailyPoint]:
    return service.daily_series(days)


@router.get("/top-products", response_model=list[TopProduct])
def top_products(
    days: int = DaysQuery,
    limit: int = Query(default=10, ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> list[TopProduct]:
    return service.top_products(days, limit)


@router.get("/top-categories", response_model=list[TopCategory])
def top_categories(
    days: int = DaysQuery,
    limit: int = Query(default=10, ge=1, le=50),
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> list[TopCategory]:
    return service.top_categories(days, limit)


@router.get("/payment-mix", response_model=list[PaymentSlice])
def payment_mix(
    days: int = DaysQuery,
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> list[PaymentSlice]:
    return service.payment_mix(days)


@router.get("/daily-report", response_model=DailyReport)
def daily_report(
    day: date | None = Query(default=None, description="Defaults to today"),
    service: AnalyticsService = Depends(get_analytics_service),
    _user: User = Depends(get_current_user),
) -> DailyReport:
    return service.daily_report(day)
