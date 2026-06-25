# Bankruptcy Feature

## 1. Purpose

A user whose net worth drops below the minimum threshold ($100) is no longer able to participate on the platform. The bankruptcy system detects this condition automatically, liquidates any remaining holdings, cancels pending auto-trades, and locks the account. The user can voluntarily recover and receive a fresh starting balance ($1,000) to continue.

---

## 2. Related Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/users/me/recover` | Recover from bankruptcy — resets balance to $1,000 |
| `GET`  | `/api/users/me` | Returns `is_bankrupt` and `bankrupt_at` for the current user |
| `POST` | `/api/trades/buy` | Triggers a bankruptcy check after every successful purchase |
| `POST` | `/api/trades/sell` | Triggers a bankruptcy check after every successful sale |

Bankruptcy is also checked during the **daily snapshot task** (`snapshot.py`), so it can be detected even without any trading activity.

---

## 3. Request and Response Examples

### Attempt to trade while bankrupt

**Request**
```
POST /api/trades/buy
Authorization: Bearer <token>

{
  "ticker": "AAPL",
  "quantity": 1
}
```

**Response `403 Forbidden`**
```json
{
  "detail": "Account is bankrupt"
}
```

---

### Recover from bankruptcy

**Request**
```
POST /api/users/me/recover
Authorization: Bearer <token>
```

**Response `200 OK`**
```json
{
  "id": 7,
  "email": "user@example.com",
  "balance": 1000.0,
  "is_bankrupt": false,
  "bankrupt_at": "2026-06-25T14:03:22",
  "registered_at": "2026-04-01T09:00:00"
}
```

> Note: `bankrupt_at` is preserved after recovery as a permanent historical record of when the event occurred.

---

### Attempt to recover when not bankrupt

**Request**
```
POST /api/users/me/recover
Authorization: Bearer <token>
```

**Response `400 Bad Request`**
```json
{
  "detail": "Account is not bankrupt"
}
```

---

### User profile showing bankruptcy state

**Request**
```
GET /api/users/me
Authorization: Bearer <token>
```

**Response `200 OK` (bankrupt user)**
```json
{
  "id": 7,
  "email": "user@example.com",
  "balance": 42.50,
  "is_bankrupt": true,
  "bankrupt_at": "2026-06-25T14:03:22",
  "registered_at": "2026-04-01T09:00:00"
}
```

---

## 4. Important Business Rules

- **Bankruptcy threshold**: net worth (cash balance + current market value of all holdings) must drop **strictly below $100** to trigger bankruptcy. A user at exactly $100 is not bankrupt.
- **Liquidation**: when bankruptcy is triggered, all holdings are sold at the current market price. If the market price cannot be fetched, `average_buy_price` is used as a fallback. Each liquidation generates a `sell` trade record in trade history.
- **Auto-trades**: all active auto-trade rules are cancelled (set to `is_active = false`) at the moment of bankruptcy.
- **Balance after liquidation**: the cash received from liquidating holdings is added to the user's balance before the account is locked. The balance will still be below $100 (otherwise bankruptcy would not have triggered), but the liquidation cash is not lost.
- **Recovery balance**: `POST /api/users/me/recover` resets the balance to **$1,000**. This is a fresh start — the user's previous trade history and `bankrupt_at` timestamp are not erased.
- **Recovery is manual**: the user must explicitly call the recovery endpoint. There is no automatic recovery.
- **`bankrupt_at` is permanent**: the field is set once on bankruptcy and is not cleared on recovery. It records the most recent bankruptcy event.
- **Idempotency**: calling `check_and_handle_bankruptcy` on an already-bankrupt user is a no-op.

---

## 5. Error Cases

| Situation | Status | Detail message |
|-----------|--------|----------------|
| Bankrupt user attempts to buy | `403` | `"Account is bankrupt"` |
| Bankrupt user attempts to sell | `403` | `"Account is bankrupt"` |
| Non-bankrupt user calls `/me/recover` | `400` | `"Account is not bankrupt"` |
| Unauthenticated request to `/me/recover` | `401` | `"Not authenticated"` |
| Market price unavailable during liquidation | — | Silently falls back to `average_buy_price`; bankruptcy still proceeds |

---

## 6. Related Database Models

### `users` table

| Column | Type | Description |
|--------|------|-------------|
| `is_bankrupt` | `Boolean` | `true` when the account is locked due to bankruptcy |
| `bankrupt_at` | `DateTime` (nullable) | UTC timestamp of the most recent bankruptcy event; `null` if the user has never gone bankrupt |
| `balance` | `Float` | Cash balance; will be < $100 at the moment of bankruptcy |

### `trades` table

Liquidation sales are recorded here with `trade_type = "sell"`. They are indistinguishable from regular sell trades in the table, but can be identified by their timestamp matching `users.bankrupt_at`.

### `holdings` table

All rows for the bankrupt user are deleted during liquidation.

### `auto_trades` table

All rows for the bankrupt user with `is_active = true` are set to `is_active = false` during bankruptcy.

> See `docs/db_schema.md` for full column listings of each table.

---

## 7. How to Test the Feature

### Unit / integration tests

All bankruptcy tests live in:

```
backend/tests/routers/test_bankruptcy.py
```

Run with:

```bash
pytest backend/tests/routers/test_bankruptcy.py -v


The test suite covers:

| Class | What is tested |
|-------|----------------|
| `TestCheckAndHandleBankruptcy` | No bankruptcy above threshold; bankruptcy triggered below threshold; holdings liquidated; multiple holdings; auto-trades cancelled; already-bankrupt user skipped; API price fallback; exact threshold edge case |
| `TestRecoverFromBankruptcy` | Balance reset to `RECOVERY_BALANCE`; `bankrupt_at` preserved; no-op for healthy user |
| `TestRecoverEndpoint` | `POST /me/recover` happy path; 400 for non-bankrupt user |
| `TestBankruptcyInTradingRoutes` | 403 on buy/sell while bankrupt; `check_and_handle_bankruptcy` called after buy and after sell; correct net worth passed to the check |

### Manual testing flow

1. Register a new user (starting balance $10,000).
2. Buy stocks until your cash balance is very low.
3. Trigger a sell that leaves net worth below $100 — the response will still be `200`, but a subsequent `GET /api/users/me` will show `"is_bankrupt": true` and a populated `bankrupt_at`.
4. Attempt another buy or sell — expect `403 Account is bankrupt`.
5. Call `POST /api/users/me/recover` — expect `200` with `balance: 1000` and `is_bankrupt: false`.
6. Verify `bankrupt_at` is still set in the response.
7. Confirm trading is possible again.

### Constants (defined in `app/services/default_services.py`)

| Constant | Value | Meaning |
|----------|-------|---------|
| `BANKRUPTCY_THRESHOLD` | `100.0` | Net worth below this triggers bankruptcy |
| `RECOVERY_BALANCE` | `1000.0` | Balance granted on recovery |
