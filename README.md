# LifeKart — Lifetime Wholesale Buying Platform

FastAPI-based modular monolith that projects and fulfills 60-year household consumption using interval storage, background workers, and Stripe payments.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Docker Compose](#docker-compose)
5. [Azure Deployment](#azure-deployment)
6. [API Modules](#api-modules)
7. [Celery Beat Tasks](#celery-beat-tasks)
8. [Core Design Decisions](#core-design-decisions)
9. [Database Indexing](#database-indexing)
10. [Technology Stack](#technology-stack)
11. [User Roles & Authorization](#user-roles--authorization)
12. [Dynamic Configuration (System Settings)](#dynamic-configuration-system-settings)
13. [KPIs & Analytics](#kpis--analytics)
14. [Environment Variables](#environment-variables)

---

## Architecture

```
                  ┌─────────────────┐
                  │   Nginx (port 80│
                  └───────┬─────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               │               ▼
   ┌─────────────┐        │     ┌─────────────────┐
   │ Next.js      │        │     │ FastAPI (async) │
   │ Frontend     │        │     │ - 14 modules    │
   │ :3000        │        │     │ - 76 routes     │
   └─────────────┘        │     │ - RBAC auth      │
                          │     │ - :8000          │
                          │     └────────┬────────┘
                          │              │
          ┌───────────────┼──────────────┼───────────────┐
          ▼               ▼              ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │PostgreSQL│   │  Redis 7 │   │  Celery   │   │  Stripe  │
   │   16     │   │ cache +  │   │  Worker   │   │ Payments │
   │          │   │ broker   │   │  + Beat   │   │          │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

14 domain modules: **Auth, Catalog, Profiling, Calculator, Agreements, Scheduling, Price Protection, Payments, Gifting, Corporate, Payroll, Community, Health, Legacy**

---

## Project Structure

```
lifekart/
├── docker-compose.yml              # Local dev (api + worker + beat + db + redis + frontend)
├── docker-compose.azure.yml        # Azure ACI prod (adds nginx, no exposed DB ports)
├── nginx/
│   └── default.conf                # Reverse proxy: /api/* → backend, /* → frontend
├── backend/
│   ├── Dockerfile                  # Multi-stage (builder + slim runtime)
│   ├── docker-compose.yml          # Backend-only docker compose
│   ├── .env.example                # Local dev environment template
│   ├── .env.production             # Azure production template
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, router mounting
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic BaseSettings
│   │   │   ├── security.py         # bcrypt + JWT create/verify
│   │   │   ├── stripe_client.py    # Stripe API wrapper
│   │   │   ├── redis.py            # Redis cache helpers
│   │   │   ├── settings_model.py   # SystemSetting model + DEFAULTS
│   │   │   └── settings_loader.py  # DB config loader with fallback
│   │   ├── db/
│   │   │   ├── base.py             # DeclarativeBase
│   │   │   └── session.py          # async engine + session factory
│   │   ├── modules/
│   │   │   ├── users/              # Auth, JWT, user management
│   │   │   ├── catalog/            # Categories, manufacturers, products, substitutes
│   │   │   ├── profiling/          # Households, members, auto health profiles
│   │   │   ├── calculator/         # Lifetime subscriptions, interval storage
│   │   │   ├── agreements/         # Wholesale contracts, sign → subscription flow
│   │   │   ├── scheduling/         # Delivery events, price history, substitution events
│   │   │   ├── price_protect/      # Price ceiling alerts, stock auto-substitution
│   │   │   ├── payments/           # Stripe methods, invoices, webhook idempotency
│   │   │   ├── gifting/            # Gift orders, activation → subscriptions
│   │   │   ├── corporate/          # Partners, approvals, employee enrollment
│   │   │   ├── payroll/            # Amortized deductions, bulk create
│   │   │   ├── community/          # Groups, auto-promote, pooled order aggregation
│   │   │   ├── health/             # Profiles, tag-based auto-swap, health rules
│   │   │   ├── legacy/             # Nominees, death verification, subscription inheritance
│   │   │   └── analytics/          # KPI snapshots, user savings, landing page stats
│   │   └── tasks/
│   │       ├── celery_app.py       # Celery instance + 9 Beat schedules
│   │       ├── analytics_tasks.py  # Weekly platform KPI snapshots
│   │       ├── calculator_tasks.py # Consumption projection generator
│   │       ├── catalog_tasks.py    # Product substitute rebuild (pure SQL)
│   │       ├── community_tasks.py  # Pooled order aggregation
│   │       ├── delivery_tasks.py   # Daily delivery + monthly invoices + archive
│   │       ├── health_tasks.py     # Pending health transition processor
│   │       ├── payroll_tasks.py    # Weekly amortized deductions
│   │       └── price_monitor.py    # Price ceiling alerts + stock substitution
│   ├── alembic/                    # Database migrations
│   ├── scripts/
│   │   ├── seed_superadmin.py      # Creates superadmin account
│   │   └── seed_catalog.py         # 78 categories, 20 products, progression rules
│   └── docs/
│       └── ARCHITECTURE.md         # Full system design document
├── frontend/
│   ├── Dockerfile                  # Multi-stage Next.js standalone build
│   ├── package.json                # Next.js 14, React 18, Tailwind
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── next.config.js              # output: 'standalone' for Docker
│   └── lib/
│       └── api.ts                  # Shared apiClient with JWT auto-attach
└── README.md
```

---

## Quick Start

```bash
# Clone and navigate
git clone <repo-url> && cd lifekart

# Backend setup
cd backend
cp .env.example .env
# Edit .env with DATABASE_URL, SECRET_KEY, Stripe keys

# Create virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start infrastructure
docker compose up -d db redis

# Run API
uvicorn app.main:app --reload

# Seed data
python scripts/seed_superadmin.py   # superadmin@lifekart.com / SuperAdmin@123
python scripts/seed_catalog.py      # 78 categories, 20 products, progression rules

# Frontend
cd ../frontend
npm install && npm run dev
```

Access API at `http://localhost:8000`, docs at `http://localhost:8000/docs`, frontend at `http://localhost:3000`.

---

## Docker Compose

### Local Development (full stack)

```bash
# From project root
docker compose up -d
```

Starts: **api**, **worker**, **beat**, **db** (PostgreSQL 16), **redis** (7), **frontend** (Next.js)

### Backend Only (development)

```bash
cd backend && docker compose up -d
```

Starts: **api** (hot-reload), **worker**, **beat**, **db**, **redis**

---

## Azure Deployment

### Prerequisites
- Azure Container Instances (ACI) or Azure VM with Docker
- Production PostgreSQL (Azure Database for PostgreSQL flexible server)
- Stripe production keys

### Single Instance Deployment (ACI)

```bash
# Set credentials
export POSTGRES_USER=lifekart_prod
export POSTGRES_PASSWORD=<strong-password>

# Copy and configure env
cp backend/.env.production backend/.env
# Edit: DATABASE_URL, SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

# Build and deploy (all services behind nginx on port 80)
docker compose -f docker-compose.azure.yml up -d

# Seed production database
docker compose -f docker-compose.azure.yml exec api python scripts/seed_superadmin.py
docker compose -f docker-compose.azure.yml exec api python scripts/seed_catalog.py
```

### Service Architecture (azure.yml)

| Service | Internal Port | Exposed | Purpose |
|---------|---------------|---------|---------|
| `nginx` | 80 | **80** (public) | Reverse proxy, routes `/api/*` → backend, `/*` → frontend |
| `api` | 8000 | Internal | FastAPI with 4 Uvicorn workers |
| `worker` | — | Internal | Celery worker (4 concurrency) |
| `beat` | — | Internal | Celery Beat scheduler |
| `db` | 5432 | Internal | PostgreSQL 16 |
| `redis` | 6379 | Internal | Redis 7 (broker + cache) |
| `frontend` | 3000 | Internal | Next.js standalone |

---

## API Modules

| # | Module | Prefix | Routes | Description |
|---|--------|--------|--------|-------------|
| 0 | **Auth** | `/api/v1/auth` | 7 | Register, login, refresh, user management, savings |
| 1 | **Catalog** | `/api/v1/catalog` | 22 | Categories, manufacturers, products, substitutes, progression rules |
| 2 | **Profiling** | `/api/v1/profiling` | 8 | Households, members, auto-creates health profiles |
| 3 | **Calculator** | `/api/v1/subscriptions` | 9 | Lifetime subscription generation + interval storage |
| 4 | **Agreements** | `/api/v1/agreements` | 9 | Wholesale contracts, sign flow → creates subscriptions |
| 5 | **Price Protection** | `/api/v1/price-protection` | 7 | Rules, price ceiling alerts, stock auto-substitution |
| 6 | **Payments** | `/api/v1/payments` | 7 | Stripe methods, invoices, webhook with idempotency |
| 7 | **Gifting** | `/api/v1/gifting` | 5 | Gift orders, activation → creates subscriptions |
| 8 | **Corporate** | `/api/v1/corporate` | 8 | Partners, approval flow, employee enrollment |
| 9 | **Payroll** | `/api/v1/payroll` | 4 | Deductions with amortization, bulk create |
| 10 | **Community** | `/api/v1/community` | 3 | Groups, auto-promote on join, pooled order aggregation |
| 11 | **Health** | `/api/v1/health` | 4 | Profiles, tag-based auto-swap, health rules |
| 12 | **Legacy** | `/api/v1/legacy` | 6 | Nominees, death verification, subscription inheritance |
| 13 | **Analytics** | `/api/v1/analytics` | 2 | Platform KPIs (superadmin), landing page stats (public) |

**Total: 101 routes** across 14 modules

---

## Celery Beat Tasks

| # | Task | Schedule | Description |
|---|------|----------|-------------|
| 1 | `process_pending_transitions` | Daily 1:00 AM | Auto-swaps products based on health condition tag rules |
| 2 | `check_stock_availability` | Daily 1:30 AM | Auto-substitutes out-of-stock/discontinued products |
| 3 | `process_daily_deliveries` | Daily 2:00 AM | Queries subscriptions due today, creates delivery events, advances cursor |
| 4 | `generate_monthly_invoices` | 1st of month 1:00 AM | Generates billing invoices from delivery events |
| 5 | `archive_old_deliveries` | Daily 3:00 AM | Archives delivery events older than 30 days |
| 6 | `check_price_ceilings` | Weekly Sun 3:00 AM | Creates price ceiling alerts for manufacturers (no auto-swap) |
| 7 | `generate_weekly_deductions` | Weekly Mon 12:30 AM | Amortized payroll deductions (annual/52) |
| 8 | `aggregate_community_orders` | Daily 11:00 PM | Aggregates household subscriptions into pooled community orders |
| 9 | `rebuild_product_substitutes` | Daily 4:00 AM | Rebuilds product substitute table using pure SQL window functions |
| 10 | `calculate_weekly_snapshot` | Weekly Sun 12:00 AM | Computes all 5 platform KPIs into a historical snapshot |

**Task ordering prevents race conditions**: health transitions (1:00 AM) run before deliveries (2:00 AM) so product swaps happen before delivery worker ships. All tasks use `engine.dispose()` in try/finally blocks to prevent connection leaks.

---

## Core Design Decisions

### Interval Storage (No Pre-Generated Deliveries)

Instead of creating 720 individual delivery rows per product (monthly × 60 years), each lifetime subscription is **one row per lifecycle phase**:

| id | product | start_date | end_date | next_delivery_date | frequency_days |
|----|---------|-----------|----------|--------------------|----------------|
| a1 | Size-S | 2026-05-07 | 2031-03-09 | 2027-05-07 | 365 |

The daily delivery worker queries `WHERE next_delivery_date = TODAY`, creates a single `delivery_event`, then advances the cursor by `frequency_days`. No pre-generation, no explosion of rows.

### Amortized Payroll

Weekly salary deductions use `total_annual_cost / weeks_per_year`, not actual deliveries that week. Prevents pay fluctuations for employees regardless of delivery schedule.

### Health Transition Ordering

Health transitions run at 1:00 AM (before deliveries at 2:00 AM), so product swaps happen before the delivery worker ships.

### Single Source of Truth

Health transitions inherit `end_date` from the subscription being removed — the health service never calculates age limits on its own.

### Tag-Based Health Auto-Swap

Products have `health_tags` (JSONB arrays like `["high_sodium", "diabetic_friendly"]`). HealthRules map `condition_name` → `forbidden_tags` + `required_tags`. When a member reports a condition, the system auto-scans all active subscriptions, identifies forbidden products, and swaps them using the catalog service.

### 60-Year Contract Lock-In

Agreements enforce exact 60-year terms using `relativedelta(years=60)` with leap-year handling. No short-term contracts allowed.

### Price Ceiling Alerts (No Auto-Swap)

When market price exceeds locked contract ceiling, the system creates alerts for manufacturers. It does NOT auto-swap — manufacturers must honor their contracts at the locked price.

### Pure SQL Substitutes Rebuild

Product substitutes are rebuilt nightly using a single PostgreSQL `ROW_NUMBER()` window function query with a `<= 0.25` price tolerance — closest price match, not cheapest.

---

## Database Indexing

- **B-tree indexes** on every foreign key column
- **GIN indexes** on all JSONB columns (`lifestyle_tags`, `existing_conditions`, `size_progression`, `health_tags`, `affected_subscriptions`)
- **Partial index** on `lifetime_subscriptions (status, next_delivery_date) WHERE status = 'active'` for the daily cursor query
- **Composite indexes** on `delivery_events`, `invoices`, and `products`

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.12+ |
| **Web Framework** | FastAPI (async) |
| **Database** | PostgreSQL 16 (+ asyncpg) |
| **Cache / Broker** | Redis 7 |
| **Task Queue** | Celery + Beat |
| **Payments** | Stripe |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Validation** | Pydantic v2 |
| **Auth** | bcrypt + python-jose (JWT) |
| **Date Math** | python-dateutil (relativedelta) |
| **Frontend** | Next.js 14, React 18, TailwindCSS |
| **Gateway** | Nginx (reverse proxy) |
| **Container** | Docker + Docker Compose |
| **Cloud** | Azure Container Instances / Azure VM |

---

## User Roles & Authorization

Roles are managed via `UserRole` enum (not raw strings) to prevent typos:

| Role | Enum | Access |
|------|------|--------|
| Customer | `UserRole.CUSTOMER` | Household management, subscriptions, agreements, gifting |
| Manufacturer | `UserRole.MANUFACTURER` | Product creation, catalog management |
| Corporate Admin | `UserRole.CORPORATE_ADMIN` | Employee enrollment, payroll deductions |
| Superadmin | `UserRole.SUPERADMIN` | User management, partner approvals, death verification, KPIs |

All protected endpoints use `Depends(require_role(UserRole.SUPERADMIN))` pattern. Public endpoints (landing page stats) have no auth requirement.

---

## Dynamic Configuration (System Settings)

Business rules are stored in the `system_settings` table, not hardcoded:

| Setting Key | Default | Used By |
|-------------|---------|---------|
| `community_discount_tiers` | 5-tier discount table | Community pooled order aggregation |
| `dietary_multipliers` | 6 dietary preferences | Calculator consumption projection |
| `lifestyle_tag_multipliers` | 7 lifestyle tags | Calculator consumption projection |
| `default_price_ceiling_pct` | 5.00% | Gifting, calculator subscriptions |
| `organic_consumption_multiplier` | 1.1× | Calculator consumption projection |
| `substitute_price_tolerance_pct` | 25.0% | Product substitute rebuild |
| `substitute_max_alternatives` | 3 | Max alternatives per product |
| `payroll_weeks_per_year` | 52 | Payroll amortization |
| `payroll_weeks_per_month` | 4.33 | Payroll max benefit calc |
| `advertised_avg_monthly_savings` | ₹5,000 | Marketing landing page |

Admins can update values via `system_settings` table — no code deployment needed.

---

## KPIs & Analytics

The `platform_metrics_snapshots` table captures weekly snapshots:

| KPI | Column | Calculation |
|-----|--------|-------------|
| Avg monthly savings | `avg_household_monthly_savings` | Σ(retail − wholesale) / active_households |
| Lifetime contracts | `lifetime_contracts_signed` | COUNT(active subscriptions) |
| Corporate partners | `active_employer_partnerships` | COUNT(active corporate partners) |
| Avg discount | `avg_wholesale_discount_pct` | AVG(community order wholesale discount) |
| Retail cost avoided | `retail_cost_avoided` | Σ(DeliveryEvent.qty × unit_price_retail) |

Computed weekly by `calculate_weekly_snapshot` Celery Beat task (Sunday midnight).

**Per-user savings**: `GET /api/v1/auth/me/savings` — live calculation, no Celery needed.

**Public landing page**: `GET /api/v1/analytics/public/landing-stats` — reads from cached snapshot + SystemSetting, no database scans.

---

## Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/lifekart

# Authentication
SECRET_KEY=<random-string-64-chars>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Business Rules (optional — defaults in SystemSetting)
MAX_LIFETIME_YEARS=60
MAX_LIFETIME_DAYS=21900
```

---

## Documentation

- Full system design, data flow diagrams, and deployment architecture: `backend/docs/ARCHITECTURE.md`