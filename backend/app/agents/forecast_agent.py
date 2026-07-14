"""Forecast Agent — reorder guidance from the forecasting service.

Single responsibility: turn per-product forecasts into a reorder shortlist.
"""
from app.schemas.agents import ForecastReport
from app.services.forecast_service import ForecastService


class ForecastAgent:
    name = "Forecast Agent"

    def __init__(self, forecast: ForecastService) -> None:
        self._forecast = forecast

    def run(self, days: int = 30) -> ForecastReport:
        forecasts = self._forecast.forecast(days)
        needs = [f for f in forecasts if f.recommended_reorder_qty > 0]
        healthy = len(forecasts) - len(needs)
        return ForecastReport(needs_reorder=needs, healthy_count=healthy)
