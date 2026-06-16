# tu-stock-exchange
TU Stock Exchange - Programmierpraktikum 2026

## Overview
A full-stack fantasy stock exchange application that simulates real-world stock trading using actual market data. The platform enables users to buy and sell stocks, track portfolio performance, compete on a leaderboard, and implement automated trading strategies.

Key Features:
- Real-time stock trading with Yahoo Finance data
- Portfolio management and historical tracking
- Competitive leaderboard system
- Automated trading 
-  engine
- Daily net worth snapshots
- User authentication and security
- Responsive web interface

## Project Structure
project-root/
├── docker-compose.yml          # Docker configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore 
- 
├── .github/
    ├── workflows               # GCP config
├── backend/                    # FastAPI backend
│   └── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── schemas/            # Database schemas
│       ├── core/               # Configuration and security
│       ├── db/                 # Database setup
│       ├── models/             # SQLAlchemy models
│       ├── routers/            # API endpoints
│       ├── services/           # Redis client and services
│       ├── tasks/              # Background tasks
│       └── utils/              # Helper utilities
├── frontend/                   # Vue.js frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── jsconfig.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.comfig.js
│   ├── vite.config.js
│   ├── public/
│   │   └── index.html          # Main HTML template
│   └── src/                    # Frontend source code
│       ├── api                 # Vue.js API
│       ├── assets/             # Static assets
│       ├── components/         # Reusable UI components
│       ├── pages/              # Visual pages
│       ├── router/             # Vue Router configuration
│       ├── stores/             # Vuex store
│       ├── App.vue             # Main application component
│       └── main.js             # Entry point
├── docs/                       # Api and database documentation
├── initdb/                     # Database initialization
│   └── init.sql                # Database schema
├── package-lock.json           # Vue.js config
├── package.json                # Vue.js dependencies
└── README.md                   # This file

## Setup Instructions
### Prerequisites
- Docker and Docker Compose (v2.0+)
- Node.js 18+ (for frontend development)
- Python 3.10+ (for backend development)

### Docker Setup (Recommended)
1. Create environment file:
    cp .env.example .env
2. Build and run containers:
    docker-compose up -d --build
3. Verify services are running:
    docker-compose ps

## Environment Configuration
Create a .env file based on .env.example with your configuration:

    # Database
    DB_USER=stock_user
    DB_PASSWORD=your_strong_password
    DB_NAME=stock_exchange

    # Redis
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_PASSWORD=

    # Security
    SECRET_KEY=your_strong_secret_key
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=60

    # API
    YAHOO_FINANCE_API=https://query1.finance.yahoo.com/v8/finance/chart

Important: The .env file should never be committed to version control (it's already in .gitignore).

## API Endpoints
### Authentication
- POST /api/auth/login - User login
- POST /api/auth/register - User registration

### Trading
- POST /api/trades/buy - Buy stocks
- POST /api/trades/sell - Sell stocks
- GET /api/portfolio - Get current portfolio
- GET /api/trades/history - Get trade history
- GET /api/portfolio/networth - Get current net worth

### Portfolio
- GET /api/users/{id}/portfolio/history - Get portfolio history

### Leaderboard
- GET /api/leaderboard - Current leaderboard (top 5 users)
- GET /api/leaderboard/history - Historical leaderboard (last 30 days)

### Auto-Trading
- POST /api/auto-trades - Create auto-trade rule
- GET /api/auto-trades - List auto-trade 
- DELETE /api/auto-trades - Delete auto-trade rule 

### Users
- GET /api/me - Show logged in user
- PUT /api/me - Commit logged in user to the database

## Database Schema Highlights
### Key Tables
- users: User accounts and balances
- holdings: Current stock positions
- trades: Trade history
- net_worth_history: Daily net worth snapshots
- auto_trades: Automatic trading rules

## Background Tasks
The application runs two critical background tasks:
1. Daily Net Worth Snapshot:
- Captures user net worth at midnight UTC
- Powers the leaderboard history feature
- Uses APScheduler with cron scheduling
2. Auto-Trade Execution:
- Checks and executes auto-trading rules hourly
- Compares current prices against user-defined targets
- Handles both buy and sell conditions

## Yahoo Finance Integration
The platform uses Yahoo Finance API for real-time stock data with:
- Redis caching (5-minute TTL) to reduce API calls
- Graceful error handling for API failures
- Rate limit management
- Fallback mechanism when API is unavailable