"""Aggregates all API routers under a single /api prefix."""
from fastapi import APIRouter

from app.api.routes import (
    agents,
    analytics,
    auth,
    categories,
    customers,
    health,
    insights,
    inventory,
    products,
    sales,
    suppliers,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(categories.router)
api_router.include_router(suppliers.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(sales.router)
api_router.include_router(inventory.router)
api_router.include_router(analytics.router)
api_router.include_router(insights.router)
api_router.include_router(agents.router)
