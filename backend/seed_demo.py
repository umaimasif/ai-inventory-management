"""Seed demo data: categories, suppliers, products, customers, 30 days of sales.

Sales are backdated so the dashboard charts have a real time series.
Safe to re-run: it clears existing demo rows first.

Usage:
    python seed_demo.py
"""
import random
from datetime import datetime, time, timedelta, date

from app.core.database import SessionLocal, Base, engine
from app import models  # noqa: F401  (register tables)
from app.models.category import Category
from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.supplier import Supplier

random.seed(42)  # deterministic demo data

CATALOG = [
    # (name, sku, category, buy, sell, stock, reorder_point)
    ("Red Shampoo", "SHM-RED", "Personal Care", 180, 260, 40, 15),
    ("White Shampoo", "SHM-WHT", "Personal Care", 170, 240, 90, 10),
    ("Conditioner", "CND-01", "Personal Care", 200, 300, 25, 12),
    ("Bread", "BRD-01", "Bakery", 60, 90, 8, 20),
    ("Butter", "BTR-01", "Dairy", 250, 340, 18, 10),
    ("Milk 1L", "MLK-01", "Dairy", 120, 165, 5, 24),
    ("Tea 250g", "TEA-01", "Beverages", 320, 430, 60, 15),
    ("Sugar 1kg", "SGR-01", "Grocery", 140, 180, 3, 20),
    ("Coffee 200g", "COF-01", "Beverages", 480, 640, 30, 10),
    ("Biscuits", "BSC-01", "Bakery", 45, 70, 120, 25),
]

# Products that sell often vs. rarely — gives the analytics something to say.
POPULARITY = {
    "BRD-01": 9, "MLK-01": 8, "TEA-01": 7, "SGR-01": 6, "BSC-01": 6,
    "BTR-01": 4, "SHM-RED": 3, "COF-01": 3, "CND-01": 2, "WHT": 1,
    "SHM-WHT": 1,
}

PAYMENTS = ["cash", "cash", "cash", "card", "mobile"]
DAYS = 30


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clear prior demo data (sale items first — FK order).
        db.query(SaleItem).delete()
        db.query(Sale).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.query(Supplier).delete()
        db.query(Customer).delete()
        db.commit()

        supplier = Supplier(name="Metro Wholesale", contact_name="Ali", phone="0300-1234567")
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        categories: dict[str, Category] = {}
        for _, _, cat_name, *_ in CATALOG:
            if cat_name not in categories:
                category = Category(name=cat_name)
                db.add(category)
                categories[cat_name] = category
        db.commit()

        products: list[Product] = []
        for name, sku, cat_name, buy, sell, stock, reorder in CATALOG:
            product = Product(
                name=name,
                sku=sku,
                category_id=categories[cat_name].id,
                supplier_id=supplier.id,
                purchase_price=buy,
                selling_price=sell,
                stock_quantity=stock,
                min_stock_level=max(reorder // 2, 1),
                reorder_point=reorder,
                safety_stock=3,
            )
            db.add(product)
            products.append(product)
        db.commit()
        for product in products:
            db.refresh(product)

        walkin = Customer(name="Walk-in", is_walkin=True)
        named = [
            Customer(name="Ayesha Khan", phone="0301-1111111"),
            Customer(name="Bilal Ahmed", phone="0302-2222222"),
            Customer(name="Fatima Noor", phone="0303-3333333"),
        ]
        db.add(walkin)
        db.add_all(named)
        db.commit()
        db.refresh(walkin)
        for customer in named:
            db.refresh(customer)

        today = date.today()
        weights = [POPULARITY.get(p.sku, 1) for p in products]
        sales_made = 0

        for offset in range(DAYS - 1, -1, -1):
            day = today - timedelta(days=offset)
            # Weekends busier; a little noise so the line isn't flat.
            base = 6 if day.weekday() >= 5 else 4
            orders_today = max(1, base + random.randint(-2, 3))

            for _ in range(orders_today):
                chosen = random.choices(products, weights=weights, k=random.randint(1, 3))
                # Dedupe so one sale doesn't list the same product twice.
                picked = {p.id: p for p in chosen}.values()

                customer = random.choice([walkin, walkin, *named])
                sale = Sale(
                    customer_id=customer.id,
                    payment_method=random.choice(PAYMENTS),
                    created_at=datetime.combine(day, time(random.randint(9, 20), 0)),
                )

                total_amount = 0.0
                total_profit = 0.0
                for product in picked:
                    qty = random.randint(1, 3)
                    unit_price = float(product.selling_price)
                    unit_cost = float(product.purchase_price)
                    line_total = unit_price * qty
                    line_profit = (unit_price - unit_cost) * qty

                    sale.items.append(
                        SaleItem(
                            product_id=product.id,
                            quantity=qty,
                            unit_price=unit_price,
                            unit_cost=unit_cost,
                            line_total=line_total,
                            line_profit=line_profit,
                        )
                    )
                    total_amount += line_total
                    total_profit += line_profit

                sale.total_amount = total_amount
                sale.total_profit = total_profit
                db.add(sale)
                sales_made += 1

        db.commit()
        print(
            f"Seeded {len(products)} products, {len(categories)} categories, "
            f"{len(named) + 1} customers, {sales_made} sales across {DAYS} days."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
