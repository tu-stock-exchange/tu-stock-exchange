# Trading Feature

## 1. Purpose

The trading system lets authenticated users buy and sell stocks at live market prices. Every trade updates the user's cash balance and their holdings record, and triggers a bankruptcy check on completion. The system also exposes endpoints for viewing the current portfolio and full trade history.

Prices are fetched from the **Finnhub API** and cached in Redis for 1 hour to avoid redundant external calls.

---

## 2. Related Endpoints

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| `POST` | `/api/trades/buy` | Yes | Buy shares of a stock |
| `POST` | `/api/trades/sell` | Yes | Sell shares of a stock |
| `GET`  | `/api/portfolio` | Yes | View all holdings with PnL breakdown |
| `GET`  | `/api/portfolio/networth` | Yes | Get total net worth (cash + stocks) |
| `GET`  | `/api/trades/history` | Yes | Paginated list of past trades |

---

## 3. Request and Response Examples

### Buy stock

**Request**
```
POST /api/trades/buy
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticker": "AAPL",
  "quantity": 5
}
```

**Response `200 OK`**
```json
{
  "message": "Buy order successful",
  "ticker": "AAPL",
  "quantity": 5,
  "price_per_stock": 150.25,
  "total_cost": 751.25,
  "new_balance": 9248.75
}
```

---

### Sell stock

**Request**
```
POST /api/trades/sell
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticker": "AAPL",
  "quantity": 3
}
```

**Response `200 OK`**
```json
{
  "message": "Sell order successful",
  "ticker": "AAPL",
  "quantity": 3,
  "price_per_stock": 155.00,
  "total_value": 465.00,
  "new_balance": 9713.75
}
```

---

### Get portfolio

**Request**
```
GET /api/portfolio
Authorization: Bearer <token>
```

**Response `200 OK`**
```json
{
  "holdings": [
    {
      "ticker": "AAPL",
      "quantity": 2,
      "average_buy_price": 150.25,
      "current_price": 155.00,
      "current_value": 310.00,
      "cost_basis": 300.50,
      "pnl": 9.50,
      "pnl_percent": 3.16
    }
  ],
  "total_current_value": 310.00,
  "total_cost_basis": 300.50,
  "total_pnl": 9.50,
  "cash_balance": 9713.75
}
```

---

### Get net worth

**Request**
```
GET /api/portfolio/networth
Authorization: Bearer <token>
```

**Response `200 OK`**
```json
{
  "networth": 10023.75,
  "cash_balance": 9713.75,
  "total_stock_value": 310.00
}
```

---

### Get trade history

**Request**
```
GET /api/trades/history?page=1&limit=10
Authorization: Bearer <token>
```

**Response `200 OK`**
```json
{
  "trades": [
    {
      "id": 1,
      "ticker": "AAPL",
      "trade_type": "buy",
      "quantity": 5,
      "price": 150.25,
      "total_value": 751.25,
      "timestamp": "2026-06-28T10:00:00"
    }
  ],
  "page": 1,
  "limit": 10
}
```

Query parameters: `page` (default `1`), `limit` (default `10`).

---

## 4. Important Business Rules

- **Live prices**: prices are fetched from Finnhub at the moment of the trade. If the price cannot be fetched (API error or unknown ticker), the trade is rejected with `503`.
- **Price caching**: Finnhub responses are cached in Redis with a 1-hour TTL (`price:<TICKER>` key). The cached price is used for subsequent requests within that window.
- **Sufficient funds**: a buy is rejected if the user's cash balance is less than `price × quantity`.
- **Sufficient holdings**: a sell is rejected if the user does not hold the ticker or holds fewer shares than requested.
- **Average buy price**: when buying a ticker the user already holds, the holding's `average_buy_price` is updated to a weighted average:
  ```
  new_avg = (existing_qty × existing_avg + new_qty × price) / (existing_qty + new_qty)
  ```
- **Holding cleanup**: when all shares of a ticker are sold (`quantity` reaches 0), the holding row is deleted.
- **Bankruptcy check**: after every successful buy or sell, `check_and_handle_bankruptcy` is called with the user's updated net worth (cash + current market value of all holdings). See `docs/bankruptcy.md` for details.
- **Bankrupt users**: a user with `is_bankrupt = true` cannot place any buy or sell orders — both endpoints return `403`.
- **Tickers are uppercased**: the stock price service normalises tickers to uppercase before querying Finnhub or Redis.

---

## 5. Error Cases

| Situation | Status | Detail message |
|-----------|--------|----------------|
| Account is bankrupt | `403` | `"Account is bankrupt"` |
| Insufficient cash balance | `400` | `"Insufficient funds. Need $X, have $Y"` |
| Not enough shares to sell | `400` | `"Not enough stocks. You have N"` |
| Price unavailable (API failure / unknown ticker) | `503` | `"Could not fetch price for <TICKER>"` |
| Missing or invalid JWT | `401` | `"Not authenticated"` |

---

## 6. Related Database Models

### `trades` table

Records every completed buy or sell. Liquidation sales triggered by bankruptcy also appear here.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `Integer` | Primary key |
| `user_id` | `Integer` | FK → `users.id` |
| `ticker` | `String` | Stock symbol (e.g. `"AAPL"`) |
| `trade_type` | `String` | `"buy"` or `"sell"` |
| `quantity` | `Integer` | Number of shares |
| `price` | `Float` | Price per share at execution time |
| `total_value` | `Float` | `price × quantity` |
| `timestamp` | `DateTime` | UTC time the trade was recorded |

### `holdings` table

Live snapshot of the user's current positions. Updated on every trade.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `Integer` | Primary key |
| `user_id` | `Integer` | FK → `users.id` |
| `ticker` | `String` | Stock symbol |
| `quantity` | `Integer` | Shares currently held |
| `average_buy_price` | `Float` | Weighted average cost per share |
| `updated_at` | `DateTime` | Last update timestamp |

> See `docs/db_schema.md` for full schema details.

### Key source files

| File | Role |
|------|------|
| `app/routers/trading.py` | All trading endpoints |
| `app/models/trade.py` | `Trade` ORM model |
| `app/models/holding.py` | `Holding` ORM model |
| `app/services/stock_price.py` | `get_current_price` — Finnhub + Redis caching |
| `app/services/default_services.py` | `check_and_handle_bankruptcy` |
| `app/core/auth_dependencies.py` | `get_current_user` dependency |

---

## 7. How to Test the Feature

### Automated tests

Trading tests live in:

```
backend/tests/routers/test_trading_router.py
```

Run with:

```bash
pytest backend/tests/routers/test_trading_router.py -v
```

The test suite covers:

| Test | What is verified |
|------|-----------------|
| `test_buy_stock_success` | Successful buy returns ticker, quantity, total cost, and new balance |
| `test_buy_stock_insufficient_funds` | `400` when balance is too low |
| `test_user_is_bankrupt` | `403` on buy when `is_bankrupt = true` |
| `test_sell_stock_success` | Successful sell returns new balance; holding reduced |
| `test_sell_stock_not_enough` | `400` when user holds fewer shares than requested |
| `test_get_portfolio_empty` | Empty holdings list; cash balance reflects starting funds |
| `test_get_portfolio_with_holdings` | PnL calculated correctly against live price mock |
| `test_get_trade_history` | Returns correct number of trades and page number |
| `test_get_networth` | Net worth = cash + (shares × current price) |

### Manual testing flow

**Buy shares**
```bash
curl -X POST http://localhost:8000/api/trades/buy \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "quantity": 5}'
```

**Sell shares**
```bash
curl -X POST http://localhost:8000/api/trades/sell \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "quantity": 2}'
```

**View portfolio**
```bash
curl http://localhost:8000/api/portfolio \
  -H "Authorization: Bearer <token>"
```

**Check net worth**
```bash
curl http://localhost:8000/api/portfolio/networth \
  -H "Authorization: Bearer <token>"
```

**View trade history (page 2)**
```bash
curl "http://localhost:8000/api/trades/history?page=2&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Configuration

| Variable | Description |
|----------|-------------|
| `FINNHUB_API_KEY` | Required. API key for live stock price lookups. |
| Redis connection | Configured via `app/services/redis_client.py`. Prices cached for 1 hour. |
