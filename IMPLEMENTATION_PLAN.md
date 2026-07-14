# Development Plan

Strategy: Build MVP first (no AI). Add AI agents one by one after core works. Defer heavy features (WhatsApp, multi-agent, ML forecasting) to later phases.

Early scheduling: use APScheduler (simple, no Redis). Move to Celery only when scale needs it.

---

Phase 1

Project setup

Authentication

Database

Backend

Frontend

---

Phase 2 (MVP core — ship this first)

Inventory CRUD

Products

Categories

Suppliers

Customers (with "Walk-in" default so sales still count)

Sales

Low-stock alerts (rule-based, no AI)

Stock audit / count endpoint (catch shrinkage)

---

Phase 3

Dashboard

Charts

KPIs

Reports

---

Phase 4

Analytics

Best sellers

Worst sellers

Frequently bought together (low min_support early; hide in UI until enough sales)

Dead stock

Inventory forecasting (rules/moving average first; ML only after ~60 days data)

---

Phase 5

AI Agents

Inventory Agent

Sales Agent

Customer Agent

Forecast Agent

Recommendation Agent

Notification Agent

Manager Assistant

---

Phase 6

Notifications (WhatsApp / Twilio) — deferred until core stable

Testing

Optimization

Deployment

Documentation