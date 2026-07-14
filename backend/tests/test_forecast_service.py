"""Unit tests for rule-based forecasting."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.schemas.insights import Confidence
from app.services.forecast_service import (
    LEAD_TIME_DAYS,
    REVIEW_PERIOD_DAYS,
    ForecastService,
)

TODAY = date(2026, 6, 15)


def _svc(db: Session) -> ForecastService:
    return ForecastService(SaleRepository(db), ProductRepository(db))


def _product(db: Session, sku: str, stock: int, safety=0) -> Product:
    p = Product(
        name=f"P-{sku}", sku=sku, purchase_price=10, selling_price=15,
        stock_quantity=stock, safety_stock=safety,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _sell(db: Session, product: Product, qty: int, on_day: date) -> None:
    sale = Sale(
        payment_method="cash",
        created_at=datetime.combine(on_day, time(12, 0)),
        total_amount=float(product.selling_price) * qty,
        total_profit=(float(product.selling_price) - float(product.purchase_price)) * qty,
    )
    sale.items.append(
        SaleItem(
            product_id=product.id, quantity=qty,
            unit_price=float(product.selling_price),
            unit_cost=float(product.purchase_price),
            line_total=float(product.selling_price) * qty,
            line_profit=(float(product.selling_price) - float(product.purchase_price)) * qty,
        )
    )
    db.add(sale)
    db.commit()


def _get(forecasts, sku):
    return next(f for f in forecasts if f.sku == sku)


def test_no_demand_product_recommends_no_reorder(db: Session) -> None:
    _product(db, "IDLE", stock=50)

    fc = _get(_svc(db).forecast(days=30, today=TODAY), "IDLE")

    assert fc.avg_daily_demand == 0.0
    assert fc.days_of_stock_left is None
    assert fc.projected_stockout_date is None
    assert fc.recommended_reorder_qty == 0
    assert fc.confidence == Confidence.low
    assert "Do not reorder" in fc.reason


def test_average_demand_and_days_left(db: Session) -> None:
    # 30 days, 2 units/day → avg 2.0/day; stock 20 → 10 days left.
    p = _product(db, "STEADY", stock=20)
    for i in range(30):
        _sell(db, p, 2, TODAY - timedelta(days=i))

    fc = _get(_svc(db).forecast(days=30, today=TODAY), "STEADY")

    assert fc.avg_daily_demand == 2.0
    assert fc.days_of_stock_left == 10.0
    assert fc.confidence == Confidence.high  # sold on all 30 days
    # Target = 2 * (7+7) + 0 = 28; reorder = ceil(28 - 20) = 8.
    assert fc.recommended_reorder_qty == 8


def test_reorder_respects_safety_stock(db: Session) -> None:
    p = _product(db, "SAFE", stock=20, safety=10)
    for i in range(30):
        _sell(db, p, 2, TODAY - timedelta(days=i))

    fc = _get(_svc(db).forecast(days=30, today=TODAY), "SAFE")

    # Target = 2 * 14 + 10 = 38; reorder = 38 - 20 = 18.
    cover = LEAD_TIME_DAYS + REVIEW_PERIOD_DAYS
    assert fc.recommended_reorder_qty == 2 * cover + 10 - 20


def test_well_stocked_product_needs_no_reorder(db: Session) -> None:
    p = _product(db, "PLENTY", stock=1000)
    for i in range(30):
        _sell(db, p, 1, TODAY - timedelta(days=i))

    fc = _get(_svc(db).forecast(days=30, today=TODAY), "PLENTY")

    assert fc.recommended_reorder_qty == 0
    assert "No reorder needed" in fc.reason


def test_confidence_tiers(db: Session) -> None:
    low = _product(db, "LOW", stock=100)
    med = _product(db, "MED", stock=100)

    _sell(db, low, 1, TODAY)  # 1 active day → low
    for i in range(7):
        _sell(db, med, 1, TODAY - timedelta(days=i))  # 7 active days → medium

    forecasts = _svc(db).forecast(days=30, today=TODAY)
    assert _get(forecasts, "LOW").confidence == Confidence.low
    assert _get(forecasts, "MED").confidence == Confidence.medium


def test_forecast_sorted_by_soonest_stockout(db: Session) -> None:
    urgent = _product(db, "URGENT", stock=4)
    relaxed = _product(db, "RELAXED", stock=100)
    for i in range(30):
        _sell(db, urgent, 2, TODAY - timedelta(days=i))  # 2 days left
        _sell(db, relaxed, 1, TODAY - timedelta(days=i))  # 100 days left

    forecasts = _svc(db).forecast(days=30, today=TODAY)
    order = [f.sku for f in forecasts]
    assert order.index("URGENT") < order.index("RELAXED")
