"""Unit tests for worst sellers, dead stock, and frequently-bought-together."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.repositories.product_repository import ProductRepository
from app.repositories.sale_repository import SaleRepository
from app.services.insights_service import MIN_SALES_FOR_FBT, InsightsService

TODAY = date(2026, 6, 15)


def _svc(db: Session) -> InsightsService:
    return InsightsService(SaleRepository(db), ProductRepository(db))


def _product(db: Session, sku: str, buy=10, sell=15, stock=100) -> Product:
    p = Product(
        name=f"P-{sku}", sku=sku, purchase_price=buy, selling_price=sell,
        stock_quantity=stock,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _sale(db: Session, items: list[tuple[Product, int]], on_day: date) -> Sale:
    """Create a sale directly (bypassing stock checks) on a given day."""
    sale = Sale(
        payment_method="cash",
        created_at=datetime.combine(on_day, time(12, 0)),
        total_amount=0,
        total_profit=0,
    )
    for product, qty in items:
        sale.items.append(
            SaleItem(
                product_id=product.id,
                quantity=qty,
                unit_price=float(product.selling_price),
                unit_cost=float(product.purchase_price),
                line_total=float(product.selling_price) * qty,
                line_profit=(float(product.selling_price) - float(product.purchase_price)) * qty,
            )
        )
    db.add(sale)
    db.commit()
    return sale


def test_worst_sellers_includes_never_sold(db: Session) -> None:
    hot = _product(db, "HOT")
    cold = _product(db, "COLD")  # never sold
    _sale(db, [(hot, 10)], TODAY)

    worst = _svc(db).worst_sellers(days=30, limit=10, today=TODAY)

    # Never-sold product ranks first (0 units).
    assert worst[0].sku == "COLD"
    assert worst[0].units_sold == 0
    assert worst[-1].sku == "HOT"


def test_dead_stock_flags_unsold_with_capital(db: Session) -> None:
    dead = _product(db, "DEAD", buy=50, stock=8)  # never sold, 8 * 50 = 400
    live = _product(db, "LIVE", stock=20)
    _sale(db, [(live, 3)], TODAY)

    items = _svc(db).dead_stock(days=30, today=TODAY)

    skus = {d.sku for d in items}
    assert "DEAD" in skus
    assert "LIVE" not in skus
    dead_row = next(d for d in items if d.sku == "DEAD")
    assert dead_row.days_since_last_sale is None
    assert dead_row.capital_tied_up == 400.0
    assert "Never sold" in dead_row.reason


def test_dead_stock_ignores_recently_sold_and_zero_stock(db: Session) -> None:
    recent = _product(db, "RECENT", stock=10)
    empty = _product(db, "EMPTY", stock=0)  # no capital tied up
    _sale(db, [(recent, 1)], TODAY - timedelta(days=2))  # within 30 days
    _sale(db, [(empty, 1)], TODAY - timedelta(days=90))  # old sale, but 0 stock

    items = _svc(db).dead_stock(days=30, today=TODAY)

    assert items == []


def test_fbt_hidden_until_enough_sales(db: Session) -> None:
    a = _product(db, "A")
    b = _product(db, "B")
    for _ in range(3):  # well under MIN_SALES_FOR_FBT
        _sale(db, [(a, 1), (b, 1)], TODAY)

    result = _svc(db).frequently_bought_together(days=30, today=TODAY)

    assert result.enough_data is False
    assert result.total_sales == 3
    assert result.min_sales_required == MIN_SALES_FOR_FBT
    assert result.pairs == []


def test_fbt_counts_pairs_and_confidence(db: Session) -> None:
    a = _product(db, "A")
    b = _product(db, "B")
    c = _product(db, "C")

    # 20 baskets total (meets threshold): 15 have A+B, 5 have A only.
    for _ in range(15):
        _sale(db, [(a, 1), (b, 1)], TODAY)
    for _ in range(5):
        _sale(db, [(a, 1), (c, 1)], TODAY)

    result = _svc(db).frequently_bought_together(days=30, today=TODAY)

    assert result.enough_data is True
    assert result.total_sales == 20

    top = result.pairs[0]
    assert {top.product_a_name, top.product_b_name} == {"P-A", "P-B"}
    assert top.together_count == 15
    assert top.support == 0.75  # 15 / 20
    # A appears in all 20 baskets, B in 15 → conf(A→B)=15/20, conf(B→A)=15/15.
    a_to_b = top.confidence_a_to_b if top.product_a_name == "P-A" else top.confidence_b_to_a
    b_to_a = top.confidence_b_to_a if top.product_a_name == "P-A" else top.confidence_a_to_b
    assert a_to_b == 0.75
    assert b_to_a == 1.0
