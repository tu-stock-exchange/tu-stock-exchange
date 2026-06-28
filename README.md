# TU Stock Exchange

Programmierpraktikum 2026 — TU Group A

A full-stack fantasy stock exchange. Users get a starting cash balance, buy and sell real stocks at live market prices, build a portfolio, and compete against each other on a leaderboard. The platform also supports rule-based auto-trading and has a bankruptcy/recovery system for users who lose too much money.

## Key Features

- **Live trading** — buy/sell real stock tickers (AAPL, TSLA, MSFT, …) at current market prices pulled from Finnhub
- **Portfolio tracking** — holdings, average buy price, P&L per position, cash balance, and total net worth
- **Leaderboard** — current top users by portfolio value, plus historical rankings over time
- **Auto-trading** — create standing buy/sell rules ("buy AAPL at $150") that execute automatically once the target price is hit
- **Bankruptcy & recovery** — accounts whose net worth drops below $100 are auto-liquidated and locked; users can opt in to a fresh $1,000 balance to start over
- **Daily net-worth snapshots** — scheduled job that powers the leaderboard history chart
- **JWT authentication** — email/password signup and login, bcrypt-hashed passwords
- **Redis-backed price caching** — reduces calls to the Finnhub API and keeps trading responsive

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 (Composition API) + Vite, Pinia, Vue Router, Vuetify, Tailwind CSS, Chart.js |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Scheduling | APScheduler (in-process background jobs) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Market data | [Finnhub](https://finnhub.io) quote API |
| Infra | Docker / Docker Compose locally, Google Cloud Run in production, GitHub Actions CI/CD |

## Project Structure

```
tu-stock-exchange/
├── docker-compose.yml           # Postgres + Redis + backend + frontend
├── .env.example                 # Environment variable template
├── .github/workflows/           # CI/CD — deploys to GCP Cloud Run on push to main
├── backend/                     # FastAPI backend
│   ├── main.py                  # App entrypoint, router wiring, scheduled jobs
│   ├── trading.py               # (legacy/standalone script, not used by the API)
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── tests/                   # pytest suite (see Testing below)
│   └── app/
│       ├── core/                # Settings, security (JWT/hashing), auth dependency
│       ├── db/                  # Engine/session setup, DB dependency
│       ├── models/               # SQLAlchemy models (users, holdings, trades, …)
│       ├── schemas/              # Pydantic request/response schemas
│       ├── routers/              # API endpoints (auth, trading, leaderboard, …)
│       ├── services/             # Finnhub client, Redis client, bankruptcy logic
│       ├── tasks/                # Scheduled jobs: daily snapshot, auto-trade executor
│       └── utils/                # Logger
├── frontend/                    # Vue 3 SPA
│   ├── Dockerfile
│   ├── nginx.conf               # Serves the built SPA in production
│   ├── vite.config.js
│   └── src/
│       ├── api/                 # Axios instance with auth interceptor
│       ├── stores/               # Pinia stores (auth)
│       ├── router/               # Vue Router + auth guard
│       ├── pages/                # Login, Register, Market, Portfolio, Dashboard,
│       │                         # Leaderboard, AutoTrades, Profile, Default (bankrupt), 
├── docs/                        # Feature-level documentation (see Documentation below)
└── reports/                     # Team progress diaries (course deliverable, not app code)
```

## Getting Started

### Prerequisites

- Docker and Docker Compose v2 (`docker compose ...`)
- Node.js 20+ (for frontend development outside Docker)
- Python 3.11+ (for backend development outside Docker)
- A free [Finnhub](https://finnhub.io/register) API key (required for live prices)

### Quick Start (Docker, recommended)

```bash
# 1. Create your environment file
cp .env.example .env
# then fill in SECRET_KEY and FINNHUB_API_KEY

# 2. Build and start everything (Postgres, Redis, backend, frontend)
docker compose up -d --build

# 3. Check that all services are healthy
docker compose ps
```

- Backend API: http://localhost:8000 (interactive docs at `/docs`)
- Frontend: http://localhost:8080

Database migrations run automatically on backend container startup (`alembic upgrade head`).

### Local Development (without Docker)

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Needs a running Postgres + Redis instance; set DATABASE_URL accordingly, e.g.:
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tu_stock_exchange
export SECRET_KEY=dev-secret
export FINNHUB_API_KEY=your_finnhub_api_key

alembic upgrade head
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev   # starts Vite dev server on http://localhost:5173
```

## Environment Configuration

Copy `.env.example` to `.env` and fill in the values. **Never commit `.env`.**

| Variable | Used by | Required | Notes |
|---|---|---|---|
| `DB_USER` | docker-compose / Postgres | Yes | Postgres username |
| `DB_PASSWORD` | docker-compose / Postgres | Yes | Postgres password |
| `DB_NAME` | docker-compose / Postgres | Yes | Database name |
| `SECRET_KEY` | backend | Yes | Signs JWT access tokens — keep private |
| `FINNHUB_API_KEY` | backend | Yes | Required to fetch live stock prices |
| `DATABASE_URL` | backend | Set by docker-compose | `postgresql+asyncpg://...`; set manually for non-Docker dev |
| `ALGORITHM` | backend | No (default `HS256`) | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | No (default `60`) | JWT token lifetime |
| `REDIS_URL` / `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | backend | No (default to the compose `redis` service) | Override for a non-Docker Redis instance |
| `LOG_TO_FILE` | backend | No (default `false`) | Write logs to file instead of stdout |

## API Reference

Base URL (Docker/local): `http://localhost:8000`. All routes below are mounted under the `/api` prefix. Interactive Swagger UI is available at `/docs` while the backend is running.

### Auth — `app/routers/auth.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | No | Create an account (starts with $10,000 balance) |
| POST | `/api/auth/login` | No | Exchange credentials for a JWT bearer token |

### Users — `app/routers/users.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/users/me` | Yes | Current user's profile |
| GET | `/api/users/{id}` | No | Public profile of any user (e.g. from the leaderboard) |
| PUT | `/api/users/me` | Yes | Update current user's email |
| POST | `/api/users/me/recover` | Yes | Recover from bankruptcy with a fresh $1,000 balance |

### Trading & Portfolio — `app/routers/trading.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/trades/buy` | Yes | Buy a quantity of a ticker at the current price |
| POST | `/api/trades/sell` | Yes | Sell a quantity of a ticker at the current price |
| GET | `/api/portfolio` | Yes | Current holdings with live value and P&L |
| GET | `/api/portfolio/networth` | Yes | Cash balance + total holdings value |
| GET | `/api/trades/history` | Yes | Paginated trade history (`page`, `limit`) |
| GET | `/api/portfolio/history` | Yes | History of user's owned stocks |

### Leaderboard — `app/routers/leaderboard.py`, `leaderboard_history.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/leaderboard` | No | Top 5 users by current portfolio value |
| GET | `/api/leaderboard/history` | No | Ranked net-worth history (`days`, default 30) |

### Auto-Trading — `app/routers/auto_trades.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auto-trades` | Yes | Create a standing buy/sell rule for a ticker + target price |
| GET | `/api/auto-trades` | Yes | List the current user's active auto-trade rules |
| DELETE | `/api/auto-trades/{id}` | Yes | Deactivate an auto-trade rule |

### Stocks — `app/routers/stocks.py`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/stocks/popular` | No | Live prices for a curated list of ~20 well-known tickers |
| GET | `/api/stocks/search?q=` | No | Search the curated list by ticker or company name |
| GET | `/api/stocks/{ticker}` | No | Current price for a single ticker |

See `docs/authentication.md` and `docs/bankruptcy.md` for full request/response examples and error cases for those two features.

## Database

PostgreSQL 15, managed with SQLAlchemy 2.0 models and Alembic migrations (`backend/alembic/versions/`). Core tables: `users`, `holdings`, `trades`, `auto_trades`, `net_worth_history`, plus `stock_price_history` and `holding_history` for time-series data. Full column-level documentation lives in `docs/db_schema.md`.

Run migrations manually with:
```bash
cd backend
alembic upgrade head
```

## Background Jobs

Started in `main.py` via APScheduler when the backend boots:

1. **Daily net-worth snapshot** (`app/tasks/snapshot.py`) — runs at 00:00 UTC, records each active user's net worth, and feeds the leaderboard history chart. Also re-checks the bankruptcy condition for every user during the same run, catching accounts that drift below the threshold without any new trades.
2. **Auto-trade execution** (`app/tasks/auto_trade_executor.py`) — runs every hour, checks all active auto-trade rules against current prices, and executes any that have hit their target.

## Bankruptcy System

If a user's net worth (cash + holdings) drops below **$100**, their holdings are automatically liquidated, any active auto-trades are cancelled, and the account is locked. The user can call `POST /api/users/me/recover` to reset to a $1,000 balance and keep playing. See `docs/bankruptcy.md` for the full rules, edge cases, and how to test it.

## Stock Price Data

Live prices come from the [Finnhub](https://finnhub.io) quote endpoint, cached in Redis for **1 hour** per ticker to limit API calls. If Finnhub or Redis is temporarily unavailable, price lookups fail gracefully (callers get `null`/`404` rather than a crash), and bankruptcy liquidation falls back to each holding's average buy price.

## Testing

Backend tests use `pytest` with an isolated SQLite database (`backend/test.db`), so no Docker services are required to run them.

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Notable suites:
- `tests/routers/test_bankruptcy.py` — bankruptcy detection, liquidation, recovery
- `tests/routers/test_trading_router.py` — buy/sell flows
- `tests/routers/test_leaderboard_router.py`, `test_leaderboard_history_router.py`
- `tests/services/test_default_services.py`, `test_stock_price_service.py`
- `tests/core/test_security.py` — password hashing and JWT

There is currently no automated frontend test suite.

## Deployment

Pushes to `main` trigger `.github/workflows/gcp-deploy.yml`, which builds and pushes both Docker images and deploys them to **Google Cloud Run** (`europe-north1`), wiring the backend to Cloud SQL (Postgres) and a private Redis instance, then deploying the frontend with the live backend URL baked in at build time.

## Documentation

The `docs/` folder has deeper write-ups for individual features:

| File | Status |
|---|---|
| `docs/authentication.md` | ✅ Complete |
| `docs/bankruptcy.md` | ✅ Complete |
| `docs/db_schema.md` | ✅ Complete |
| `docs/api.md` | ⚠️ Partial |
| `docs/trading.md`, `docs/leaderboard.md`, `docs/portfolio.md`, `docs/auto_trades.md`, `docs/testing.md` | 📝 Placeholder, not yet written |
