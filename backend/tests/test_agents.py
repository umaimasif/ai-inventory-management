"""Unit tests for the multi-agent AI layer.

No LLM is configured in the test environment, so `llm_used` is always False and
the deterministic template answers are exercised — which is exactly what we want
to assert about grounding.
"""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.agents.customer_agent import CustomerAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.manager_assistant import ManagerAssistant
from app.agents.notification_agent import NotificationAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.models.category import Category
from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.stock_audit_repository import StockAuditRepository
from app.schemas.agents import CustomerSegment, Priority, Severity
from app.services.analytics_service import AnalyticsService
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService
from app.services.inventory_service import InventoryService

TODAY = date(2026, 6, 15)


# --- fixtures / builders -----------------------------------------------


def _product(db, sku, stock, sell=15, buy=10, reorder=0, category=None):
    p = Product(
        name=f"P-{sku}", sku=sku, purchase_price=buy, selling_price=sell,
        stock_quantity=stock, reorder_point=reorder, category_id=category,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _customer(db, name, created_days_ago=100, walkin=False):
    c = Customer(name=name, is_walkin=walkin)
    db.add(c)
    db.commit()
    db.refresh(c)
    c.created_at = datetime.combine(TODAY - timedelta(days=created_days_ago), time(9, 0))
    db.commit()
    db.refresh(c)
    return c


def _sale(db, customer, items, on_day):
    sale = Sale(
        customer_id=customer.id if customer else None,
        payment_method="cash",
        created_at=datetime.combine(on_day, time(12, 0)),
        total_amount=0, total_profit=0,
    )
    total = 0.0
    for product, qty in items:
        line = float(product.selling_price) * qty
        sale.items.append(
            SaleItem(
                product_id=product.id, quantity=qty,
                unit_price=float(product.selling_price),
                unit_cost=float(product.purchase_price),
                line_total=line,
                line_profit=(float(product.selling_price) - float(product.purchase_price)) * qty,
            )
        )
        total += line
    sale.total_amount = total
    db.add(sale)
    db.commit()
    return sale


def _forecast(db):
    return ForecastService(SaleRepository(db), ProductRepository(db))


def _insights(db):
    return InsightsService(SaleRepository(db), ProductRepository(db))


def _analytics(db):
    return AnalyticsService(SaleRepository(db), ProductRepository(db))


def _inventory(db):
    return InventoryService(
        ProductRepository(db), CustomerRepository(db),
        SaleRepository(db), StockAuditRepository(db),
    )


# --- Customer Intelligence Agent ---------------------------------------


def test_customer_segmentation(db: Session) -> None:
    p = _product(db, "A", stock=1000, sell=100, buy=40)

    vip = _customer(db, "VIP", created_days_ago=100)
    regular = _customer(db, "Regular", created_days_ago=100)
    newbie = _customer(db, "Newbie", created_days_ago=5)
    inactive = _customer(db, "Inactive", created_days_ago=200)
    _customer(db, "Walk-in", walkin=True)

    # VIP: big recent spend.
    _sale(db, vip, [(p, 100)], TODAY)          # 10,000
    # Regular: modest recent spend, old signup.
    _sale(db, regular, [(p, 20)], TODAY)       # 2,000
    # New: signed up 5 days ago, one small order.
    _sale(db, newbie, [(p, 5)], TODAY)         # 500
    # Inactive: last purchase 90 days ago.
    _sale(db, inactive, [(p, 10)], TODAY - timedelta(days=90))

    segments = CustomerAgent(CustomerRepository(db), SaleRepository(db)).run(TODAY)

    by_name = {c.name: c for c in segments.customers}
    assert by_name["VIP"].segment == CustomerSegment.vip
    assert by_name["Regular"].segment == CustomerSegment.regular
    assert by_name["Newbie"].segment == CustomerSegment.new
    assert by_name["Inactive"].segment == CustomerSegment.inactive

    # Walk-in is excluded from segmentation entirely.
    assert "Walk-in" not in by_name
    # Sorted by spend, VIP first.
    assert segments.customers[0].name == "VIP"


def test_customer_favorite_category(db: Session) -> None:
    cat = Category(name="Drinks")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    drink = _product(db, "D", stock=100, category=cat.id)
    other = _product(db, "O", stock=100)
    cust = _customer(db, "Buyer")
    _sale(db, cust, [(drink, 10), (other, 1)], TODAY)

    segments = CustomerAgent(CustomerRepository(db), SaleRepository(db)).run(TODAY)
    assert segments.customers[0].favorite_category == "Drinks"


# --- Recommendation Agent ----------------------------------------------


def test_recommendations_include_restock_and_clearance(db: Session) -> None:
    # High-demand, low-stock product → restock recommendation.
    hot = _product(db, "HOT", stock=4)
    for i in range(30):
        _sale(db, None, [(hot, 2)], TODAY - timedelta(days=i))

    # Product with stock but no sales → dead stock → clearance recommendation.
    _product(db, "DEAD", stock=10, buy=100)

    recs = RecommendationAgent(_forecast(db), _insights(db)).run(days=30, today=TODAY)

    categories = {r.category for r in recs}
    assert "restock" in categories
    assert "clearance" in categories

    restock = next(r for r in recs if r.category == "restock")
    assert restock.priority == Priority.high  # ~2 days of stock left
    assert restock.reason  # always explains why

    # High priority sorts first.
    assert recs[0].priority == Priority.high


# --- Notification Agent ------------------------------------------------


def test_alerts_flag_out_of_stock(db: Session) -> None:
    _product(db, "EMPTY", stock=0, reorder=5)
    agent = NotificationAgent(
        _analytics(db), _inventory(db), _forecast(db),
        RecommendationAgent(_forecast(db), _insights(db)),
    )
    alerts = agent.alerts(days=30, today=TODAY)
    assert any(a.severity == Severity.critical for a in alerts)


def test_morning_report_uses_template_without_llm(db: Session) -> None:
    p = _product(db, "A", stock=100)
    _sale(db, None, [(p, 3)], TODAY)

    agent = NotificationAgent(
        _analytics(db), _inventory(db), _forecast(db),
        RecommendationAgent(_forecast(db), _insights(db)),
    )
    report = agent.morning_report(day=TODAY)

    assert report.llm_used is False  # no GROQ_API_KEY in tests
    assert "Good morning" in report.narrative


# --- Manager Assistant (grounding) -------------------------------------


def _assistant(db) -> ManagerAssistant:
    return ManagerAssistant(
        _analytics(db), _insights(db), _forecast(db),
        CustomerAgent(CustomerRepository(db), SaleRepository(db)),
    )


def test_assistant_restock_intent_is_grounded(db: Session) -> None:
    hot = _product(db, "HOT", stock=4)
    for i in range(30):
        _sale(db, None, [(hot, 2)], TODAY - timedelta(days=i))

    resp = _assistant(db).ask("What should I order today?", today=TODAY)

    assert resp.intent == "restock"
    assert resp.llm_used is False
    # The answer is built from real facts, exposed for transparency.
    assert "products_to_reorder" in resp.grounded_on
    assert resp.grounded_on["products_to_reorder"][0]["name"] == "P-HOT"
    assert "P-HOT" in resp.answer


def test_assistant_top_customers_intent(db: Session) -> None:
    p = _product(db, "A", stock=1000, sell=100)
    cust = _customer(db, "Big Spender")
    _sale(db, cust, [(p, 50)], TODAY)

    resp = _assistant(db).ask("Which customers spend the most?", today=TODAY)

    assert resp.intent == "top_customers"
    assert resp.grounded_on["top_spenders"][0]["name"] == "Big Spender"
    assert "Big Spender" in resp.answer


def test_assistant_sales_trend_intent(db: Session) -> None:
    p = _product(db, "A", stock=1000)
    _sale(db, None, [(p, 5)], TODAY)

    resp = _assistant(db).ask("Why are sales down?", today=TODAY)
    assert resp.intent == "sales_trend"
    assert "change_pct" in resp.grounded_on


def test_assistant_falls_back_to_summary(db: Session) -> None:
    resp = _assistant(db).ask("Tell me how the shop is doing", today=TODAY)
    assert resp.intent == "summary"
    assert "revenue" in resp.grounded_on


# --- Inventory Agent ---------------------------------------------------


def test_inventory_agent_reports_out_of_stock(db: Session) -> None:
    _product(db, "EMPTY", stock=0, reorder=5)
    agent = InventoryAgent(_inventory(db), _insights(db), ProductRepository(db))
    report = agent.run()
    assert any(f.severity == Severity.critical for f in report.findings)
