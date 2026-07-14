"""Unit tests for analytics aggregation."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.services.analytics_service import AnalyticsService
from app.services.sales_service import SalesService

TODAY = date(2026, 6, 15)


def _analytics(db: Session) -> AnalyticsService:
    return AnalyticsService(SaleRepository(db), ProductRepository(db))


def _sell(db: Session, product: Product, qty: int, on_day: date, payment="cash") -> Sale:
    """Record a sale and backdate it to `on_day` (noon)."""
    service = SalesService(
        db, SaleRepository(db), ProductRepository(db), CustomerRepository(db)
    )
    sale = service.create(
        SaleCreate(
            payment_method=payment,
            items=[SaleItemCreate(product_id=product.id, quantity=qty)],
        )
    )
    sale.created_at = datetime.combine(on_day, time(12, 0))
    db.commit()
    db.refresh(sale)
    return sale


def _product(db: Session, sku: str, buy: float, sell: float, stock=1000, category=None):
    product = Product(
        name=f"P-{sku}",
        sku=sku,
        purchase_price=buy,
        selling_price=sell,
        stock_quantity=stock,
        category_id=category,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_kpis_current_vs_previous_period(db: Session) -> None:
    p = _product(db, "A", buy=10, sell=15)  # profit 5/unit

    # Current window (last 7 days incl. today): 2 units on TODAY.
    _sell(db, p, 2, TODAY)
    # Previous window (the 7 days before that): 1 unit, 10 days ago.
    _sell(db, p, 1, TODAY - timedelta(days=10))

    kpis = _analytics(db).kpis(days=7, today=TODAY)

    assert kpis.revenue.current == 30.0  # 15 * 2
    assert kpis.revenue.previous == 15.0  # 15 * 1
    assert kpis.revenue.change_pct == 100.0
    assert kpis.profit.current == 10.0  # 5 * 2
    assert kpis.orders.current == 1
    assert kpis.units_sold.current == 2
    assert kpis.avg_order_value.current == 30.0


def test_kpis_change_pct_is_none_when_previous_is_zero(db: Session) -> None:
    p = _product(db, "A", buy=1, sell=2)
    _sell(db, p, 1, TODAY)

    kpis = _analytics(db).kpis(days=7, today=TODAY)

    assert kpis.revenue.previous == 0.0
    assert kpis.revenue.change_pct is None


def test_daily_series_is_zero_filled_and_ordered(db: Session) -> None:
    p = _product(db, "A", buy=10, sell=15)
    _sell(db, p, 3, TODAY - timedelta(days=2))

    series = _analytics(db).daily_series(days=5, today=TODAY)

    assert len(series) == 5
    assert [pt.day for pt in series] == sorted(pt.day for pt in series)
    assert series[-1].day == TODAY

    hit = next(pt for pt in series if pt.day == TODAY - timedelta(days=2))
    assert hit.revenue == 45.0
    assert hit.units == 3
    assert hit.orders == 1

    # Every other day is zero-filled.
    assert sum(pt.orders for pt in series) == 1


def test_daily_series_excludes_sales_outside_window(db: Session) -> None:
    p = _product(db, "A", buy=10, sell=15)
    _sell(db, p, 5, TODAY - timedelta(days=30))  # far outside a 5-day window

    series = _analytics(db).daily_series(days=5, today=TODAY)

    assert sum(pt.revenue for pt in series) == 0.0


def test_top_products_ranked_by_units(db: Session) -> None:
    a = _product(db, "A", buy=10, sell=15)
    b = _product(db, "B", buy=1, sell=2)
    _sell(db, a, 2, TODAY)
    _sell(db, b, 9, TODAY)

    top = _analytics(db).top_products(days=7, limit=10, today=TODAY)

    assert [t.sku for t in top] == ["B", "A"]
    assert top[0].units_sold == 9
    assert top[1].revenue == 30.0
    assert top[1].profit == 10.0


def test_top_categories_groups_and_labels_uncategorized(db: Session) -> None:
    cat = Category(name="Drinks")
    db.add(cat)
    db.commit()
    db.refresh(cat)

    in_cat = _product(db, "A", buy=10, sell=20, category=cat.id)
    no_cat = _product(db, "B", buy=1, sell=2)
    _sell(db, in_cat, 3, TODAY)  # revenue 60
    _sell(db, no_cat, 1, TODAY)  # revenue 2

    top = _analytics(db).top_categories(days=7, today=TODAY)

    assert top[0].name == "Drinks"
    assert top[0].revenue == 60.0
    assert top[1].name == "Uncategorized"
    assert top[1].category_id is None


def test_payment_mix(db: Session) -> None:
    p = _product(db, "A", buy=10, sell=15)
    _sell(db, p, 2, TODAY, payment="cash")  # 30
    _sell(db, p, 4, TODAY, payment="card")  # 60

    mix = _analytics(db).payment_mix(days=7, today=TODAY)

    assert [m.payment_method for m in mix] == ["card", "cash"]
    assert mix[0].revenue == 60.0
    assert mix[0].orders == 1


def test_daily_report_covers_only_that_day(db: Session) -> None:
    p = _product(db, "A", buy=10, sell=15, stock=100)
    _sell(db, p, 2, TODAY)
    _sell(db, p, 7, TODAY - timedelta(days=1))

    report = _analytics(db).daily_report(day=TODAY)

    assert report.day == TODAY
    assert report.revenue == 30.0
    assert report.profit == 10.0
    assert report.orders == 1
    assert report.units_sold == 2
    assert report.top_products[0].sku == "A"
    assert report.top_products[0].units_sold == 2
