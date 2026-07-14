"""Schemas for the multi-agent AI layer (Phase 5).

Every agent emits structured findings/recommendations with a `reason`. The
Manager Assistant and reports may optionally phrase these with an LLM, but the
facts themselves are always computed deterministically from the database.
"""
from enum import Enum

from pydantic import BaseModel

from app.schemas.analytics import DailyReport
from app.schemas.insights import ProductForecast


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class CustomerSegment(str, Enum):
    vip = "vip"
    regular = "regular"
    new = "new"
    inactive = "inactive"


# --- Agent findings -----------------------------------------------------


class Finding(BaseModel):
    """A single observation from an agent, with the reasoning behind it."""

    title: str
    detail: str
    severity: Severity = Severity.info


class AgentReport(BaseModel):
    """A named agent's set of findings."""

    agent: str
    findings: list[Finding]


class Recommendation(BaseModel):
    """An actionable recommendation. Always explains WHY."""

    title: str
    reason: str
    priority: Priority
    category: str  # e.g. "restock", "clearance", "bundle", "promotion"


# --- Customer intelligence ----------------------------------------------


class CustomerInsight(BaseModel):
    customer_id: int
    name: str
    segment: CustomerSegment
    total_spent: float
    orders: int
    days_since_last_purchase: int | None
    favorite_category: str | None
    reason: str


class CustomerSegments(BaseModel):
    counts: dict[str, int]
    customers: list[CustomerInsight]


# --- Alerts & report ----------------------------------------------------


class Alert(BaseModel):
    title: str
    detail: str
    severity: Severity


class MorningReport(BaseModel):
    """The daily business summary. `narrative` is LLM- or template-phrased."""

    report: DailyReport
    recommendations: list[Recommendation]
    alerts: list[Alert]
    narrative: str
    llm_used: bool


# --- Manager assistant --------------------------------------------------


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    intent: str
    grounded_on: dict  # the exact facts used to answer — full transparency
    llm_used: bool


# --- Forecast passthrough (for the agents namespace) --------------------


class ForecastReport(BaseModel):
    needs_reorder: list[ProductForecast]
    healthy_count: int
