"""Shared FastAPI dependencies (DI wiring)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.stock_audit_repository import StockAuditRepository
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.user_repository import UserRepository
from app.agents.customer_agent import CustomerAgent
from app.agents.forecast_agent import ForecastAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.manager_assistant import ManagerAssistant
from app.agents.notification_agent import NotificationAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.sales_agent import SalesAgent
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService
from app.services.customer_service import CustomerService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.sales_service import SalesService
from app.services.supplier_service import SupplierService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# --- Auth ---------------------------------------------------------------


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(
    users: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(users)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    """Resolve the authenticated user from the bearer token."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    subject = decode_access_token(token)
    if subject is None:
        raise credentials_error

    user = users.get_by_id(int(subject))
    if user is None:
        raise credentials_error
    return user


# --- Domain services ----------------------------------------------------


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(CategoryRepository(db))


def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    return SupplierService(SupplierRepository(db))


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(CustomerRepository(db))


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(
        ProductRepository(db),
        CategoryRepository(db),
        SupplierRepository(db),
    )


def get_sales_service(db: Session = Depends(get_db)) -> SalesService:
    return SalesService(
        db,
        SaleRepository(db),
        ProductRepository(db),
        CustomerRepository(db),
    )


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(SaleRepository(db), ProductRepository(db))


def get_insights_service(db: Session = Depends(get_db)) -> InsightsService:
    return InsightsService(SaleRepository(db), ProductRepository(db))


def get_forecast_service(db: Session = Depends(get_db)) -> ForecastService:
    return ForecastService(SaleRepository(db), ProductRepository(db))


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(
        ProductRepository(db),
        CustomerRepository(db),
        SaleRepository(db),
        StockAuditRepository(db),
    )


# --- AI agents (Phase 5) ------------------------------------------------
# Agents compose the deterministic services above. Each is a single
# responsibility; the Recommendation, Notification and Manager agents fan in.


def get_inventory_agent(db: Session = Depends(get_db)) -> InventoryAgent:
    return InventoryAgent(
        get_inventory_service(db),
        get_insights_service(db),
        ProductRepository(db),
    )


def get_sales_agent(db: Session = Depends(get_db)) -> SalesAgent:
    return SalesAgent(get_analytics_service(db), get_insights_service(db))


def get_customer_agent(db: Session = Depends(get_db)) -> CustomerAgent:
    return CustomerAgent(CustomerRepository(db), SaleRepository(db))


def get_forecast_agent(db: Session = Depends(get_db)) -> ForecastAgent:
    return ForecastAgent(get_forecast_service(db))


def get_recommendation_agent(db: Session = Depends(get_db)) -> RecommendationAgent:
    return RecommendationAgent(get_forecast_service(db), get_insights_service(db))


def get_notification_agent(db: Session = Depends(get_db)) -> NotificationAgent:
    return NotificationAgent(
        get_analytics_service(db),
        get_inventory_service(db),
        get_forecast_service(db),
        get_recommendation_agent(db),
    )


def get_manager_assistant(db: Session = Depends(get_db)) -> ManagerAssistant:
    return ManagerAssistant(
        get_analytics_service(db),
        get_insights_service(db),
        get_forecast_service(db),
        get_customer_agent(db),
    )
