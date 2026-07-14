"""Multi-agent AI routes (Phase 5)."""
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_current_user,
    get_customer_agent,
    get_forecast_agent,
    get_inventory_agent,
    get_manager_assistant,
    get_notification_agent,
    get_recommendation_agent,
    get_sales_agent,
)
from app.agents.customer_agent import CustomerAgent
from app.agents.forecast_agent import ForecastAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.manager_assistant import ManagerAssistant
from app.agents.notification_agent import NotificationAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.sales_agent import SalesAgent
from app.models.user import User
from app.schemas.agents import (
    AgentReport,
    Alert,
    ChatRequest,
    ChatResponse,
    CustomerSegments,
    ForecastReport,
    MorningReport,
    Recommendation,
)

router = APIRouter(prefix="/agents", tags=["agents"])

DaysQuery = Query(default=30, ge=1, le=365)


@router.get("/inventory", response_model=AgentReport)
def inventory_agent(
    agent: InventoryAgent = Depends(get_inventory_agent),
    _user: User = Depends(get_current_user),
) -> AgentReport:
    return agent.run()


@router.get("/sales", response_model=AgentReport)
def sales_agent(
    days: int = DaysQuery,
    agent: SalesAgent = Depends(get_sales_agent),
    _user: User = Depends(get_current_user),
) -> AgentReport:
    return agent.run(days)


@router.get("/customers", response_model=CustomerSegments)
def customer_agent(
    agent: CustomerAgent = Depends(get_customer_agent),
    _user: User = Depends(get_current_user),
) -> CustomerSegments:
    return agent.run()


@router.get("/forecast", response_model=ForecastReport)
def forecast_agent(
    days: int = DaysQuery,
    agent: ForecastAgent = Depends(get_forecast_agent),
    _user: User = Depends(get_current_user),
) -> ForecastReport:
    return agent.run(days)


@router.get("/recommendations", response_model=list[Recommendation])
def recommendations(
    days: int = DaysQuery,
    agent: RecommendationAgent = Depends(get_recommendation_agent),
    _user: User = Depends(get_current_user),
) -> list[Recommendation]:
    return agent.run(days)


@router.get("/alerts", response_model=list[Alert])
def alerts(
    days: int = DaysQuery,
    agent: NotificationAgent = Depends(get_notification_agent),
    _user: User = Depends(get_current_user),
) -> list[Alert]:
    return agent.alerts(days)


@router.get("/report", response_model=MorningReport)
def morning_report(
    day: date | None = Query(default=None, description="Defaults to today"),
    agent: NotificationAgent = Depends(get_notification_agent),
    _user: User = Depends(get_current_user),
) -> MorningReport:
    return agent.morning_report(day)


@router.post("/assistant/chat", response_model=ChatResponse)
def assistant_chat(
    payload: ChatRequest,
    agent: ManagerAssistant = Depends(get_manager_assistant),
    _user: User = Depends(get_current_user),
) -> ChatResponse:
    return agent.ask(payload.question)
