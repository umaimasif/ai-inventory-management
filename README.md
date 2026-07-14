---
title: AI Inventory Management
emoji: 📦
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

<!-- The YAML block above configures the Hugging Face Space. See DEPLOY.md. -->

# AI Inventory Management System

An AI-powered inventory management system that acts as an intelligent business
assistant. See the design docs in the repo root: [SKILL.md](SKILL.md),
[AI_ARCHITECTURE.md](AI_ARCHITECTURE.md), [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md),
[API_SPEC.md](API_SPEC.md), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md),
and [coding_rules.md](coding_rules.md).

**Deploying?** See [DEPLOY.md](DEPLOY.md).

## Status: Phases 1–5 complete

- **Phase 1** — Project setup, authentication (JWT + bcrypt), database, backend
  API, frontend shell.
- **Phase 2** — Products, categories, suppliers, customers, sales (stock
  decrement + profit, atomic), low-stock alerts, stock audits.
- **Phase 3** — Dashboard KPIs with period-over-period deltas, revenue/profit
  charts, top products & categories, payment mix, daily report.
- **Phase 4** — Worst sellers, dead-stock detection (capital tied up),
  frequently-bought-together (market basket, hidden until enough sales), and
  rule-based demand forecasting with reorder guidance + confidence labels.
- **Phase 5** — Seven collaborating AI agents (Inventory, Sales, Customer,
  Forecast, Recommendation, Notification, Manager Assistant), a grounded
  natural-language assistant, and a daily AI briefing. LLM phrasing is optional
  (Groq); the system is fully functional without an API key.

- **Backend** — FastAPI + SQLAlchemy 2.0, Clean Architecture
  (api / services / repositories / models / schemas / core / agents).
  Database is configurable via `DATABASE_URL` — SQLite by default for local dev,
  PostgreSQL for production.
- **Frontend** — Next.js 16 (App Router) + React 19 + Tailwind 4 + Recharts.
  Login, register, dashboard, products, sales, customers, categories, suppliers,
  reports.

### Demo data

To populate the dashboard with 30 days of sales so the charts have something to
show:

```bash
cd backend
python seed_demo.py
```

This **replaces** products, categories, suppliers, customers, and sales. It does
not touch user accounts.

## Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL (optional — SQLite works out of the box for local dev)

## Backend — run

```bash
cd backend
python -m venv .venv
# Windows:
.venv/Scripts/activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # then edit .env as needed

uvicorn app.main:app --reload --port 8000
```

- API base: `http://localhost:8000`
- Interactive docs (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### Auth endpoints (Phase 1)

| Method | Path                 | Purpose                    |
| ------ | -------------------- | -------------------------- |
| POST   | `/api/auth/register` | Create account, get token  |
| POST   | `/api/auth/login`    | Log in, get token          |
| GET    | `/api/auth/me`       | Current user (bearer auth) |

### Resource endpoints (Phase 2)

All require a bearer token.

| Method              | Path                              | Purpose                       |
| ------------------- | --------------------------------- | ----------------------------- |
| GET/POST/PUT/DELETE | `/api/products`                   | Product CRUD                  |
| POST                | `/api/products/{id}/adjust-stock` | Restock / correct stock       |
| GET/POST/PUT/DELETE | `/api/categories`                 | Category CRUD                 |
| GET/POST/PUT/DELETE | `/api/suppliers`                  | Supplier CRUD                 |
| GET/POST/PUT/DELETE | `/api/customers`                  | Customer CRUD                 |
| GET/POST            | `/api/sales`                      | Record + list sales           |
| GET                 | `/api/inventory/summary`          | KPI counts                    |
| GET                 | `/api/inventory/low-stock`        | Products below reorder point  |
| GET/POST            | `/api/inventory/audits`           | Physical stock counts         |

### Analytics endpoints (Phase 3)

| Method | Path                            | Purpose                            |
| ------ | ------------------------------- | ---------------------------------- |
| GET    | `/api/analytics/kpis`           | Revenue/profit/orders + deltas     |
| GET    | `/api/analytics/daily`          | Daily series (zero-filled)         |
| GET    | `/api/analytics/top-products`   | Best sellers                       |
| GET    | `/api/analytics/top-categories` | Category breakdown                 |
| GET    | `/api/analytics/payment-mix`    | Revenue share by payment method    |
| GET    | `/api/analytics/daily-report`   | One day's business summary         |

All accept `?days=N` (1–365, default 30); `daily-report` accepts `?day=YYYY-MM-DD`.

### Insight & forecast endpoints (Phase 4)

| Method | Path                                          | Purpose                              |
| ------ | --------------------------------------------- | ------------------------------------ |
| GET    | `/api/insights/worst-sellers`                 | Slowest movers (incl. never-sold)    |
| GET    | `/api/insights/dead-stock`                    | Unsold stock + capital tied up       |
| GET    | `/api/insights/frequently-bought-together`    | Market-basket pairs (gated on data)  |
| GET    | `/api/insights/forecast`                      | Demand + reorder qty + confidence    |

Forecasting is a **moving average**, not ML — each row carries a `confidence`
(low/medium/high) from how much history backs it, and a plain-language `reason`.
Swap in a trained model once ~60+ days of history exist.

### AI agent endpoints (Phase 5)

| Method | Path                          | Agent / purpose                          |
| ------ | ----------------------------- | ---------------------------------------- |
| GET    | `/api/agents/inventory`       | Inventory Agent — stock health findings  |
| GET    | `/api/agents/sales`           | Sales Agent — trends & best/worst        |
| GET    | `/api/agents/customers`       | Customer Agent — VIP/regular/new/inactive|
| GET    | `/api/agents/forecast`        | Forecast Agent — reorder shortlist       |
| GET    | `/api/agents/recommendations` | Recommendation Agent — reasoned actions  |
| GET    | `/api/agents/alerts`          | Notification Agent — smart alerts        |
| GET    | `/api/agents/report`          | Notification Agent — daily morning report|
| POST   | `/api/agents/assistant/chat`  | Manager Assistant — grounded NL Q&A      |

**Grounding.** Every number comes from a deterministic database query. The LLM
(optional, via `GROQ_API_KEY`) only *phrases* facts it is handed and is
instructed to use nothing else — it never queries the database or invents
figures. The assistant returns `grounded_on` (the exact facts used) and
`llm_used` so answers are fully auditable. With no key set, agents use
deterministic template wording and remain fully functional.

To enable LLM phrasing:

```bash
# backend/.env
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### Backend — tests

```bash
cd backend
pytest              # unit tests
python smoke_test.py  # in-process end-to-end auth flow
```

## Frontend — run

```bash
cd frontend
npm install                 # already installed if scaffolded
cp .env.example .env.local  # NEXT_PUBLIC_API_URL points at the backend

npm run dev                 # http://localhost:3000
```

Open `http://localhost:3000` → redirects to `/login`. Register an account,
then land on the dashboard.

### Frontend — build

```bash
cd frontend
npm run build
```

## Configuration

**backend/.env**

| Variable                      | Default                      | Notes                          |
| ----------------------------- | ---------------------------- | ------------------------------ |
| `DATABASE_URL`                | `sqlite:///./inventory.db`   | Use `postgresql+psycopg2://…`  |
| `JWT_SECRET_KEY`              | change me                    | Long random string in prod     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                         | Token lifetime                 |
| `FRONTEND_ORIGIN`             | `http://localhost:3000`      | CORS allowlist                 |

**frontend/.env.local**

| Variable              | Default                 |
| --------------------- | ----------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

## Notes / next phases

- Tables are auto-created on backend startup for convenience. Replace with
  **Alembic** migrations before production.
- Auth token is stored client-side (localStorage) for Phase 1 simplicity.
- Phase 2 onward: products, categories, suppliers, customers, sales, dashboards,
  analytics, then the AI agents. See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
