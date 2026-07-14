Tables

Users

Products

Categories

Inventory

Sales

Sale Items

Customers

Suppliers

Purchase Orders

Inventory Logs

Notifications

Recommendations

Forecasts

Customer Insights

Agent Logs

Product Batches

Stock Audits

---

Additional Fields

Products
- min_stock_level
- reorder_point
- safety_stock

Product Batches (per-batch expiry tracking)
- product_id (FK)
- batch_number / lot_number
- quantity
- expiry_date
- received_date

Note: Expiry must be tracked per batch, not per product. Same product can have multiple expiry dates.

Stock Audits (detect inventory loss / shrinkage)
- product_id (FK)
- system_count
- physical_count
- difference
- audited_at
- note

Note: Inventory loss = physical_count < system_count.

---

Every table should include

id

created_at

updated_at

Indexes

Foreign keys

Soft delete support where appropriate.