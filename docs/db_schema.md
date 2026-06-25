# Database Schema

Base: PostgreSQL 15. ORM: SQLAlchemy 2.0. Migrations: Alembic.

---

## Tables

### `users`

Stores registered users and their account state.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `email` | `String` | No | — | Unique, lowercased on write |
| `username` | `String` | Yes | — | Unique display name |
| `password_hash` | `String` | No | — | bcrypt hash, never stored in plain text |
| `balance` | `Float` | No | `10000.0` | Cash balance in USD |
| `is_bankrupt` | `Boolean` | No | `false` | `true` when account is locked due to bankruptcy |
| `bankrupt_at` | `DateTime` | Yes | `null` | UTC timestamp of the most recent bankruptcy event |
| `registered_at` | `DateTime` | No | `utcnow` | Account creation time |

**Relationships:** one user → many `holdings`, `trades`, `auto_trades`, `net_worth_history`

---

### `holdings`

Current portfolio snapshot, one row per user per ticker. Updated after every buy/sell. Deleted when quantity reaches zero or on bankruptcy liquidation.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `user_id` | `Integer` | No | — | FK → `users.id` |
| `ticker` | `String` | No | — | Stock symbol (e.g. `AAPL`) |
| `quantity` | `Integer` | No | — | Number of shares currently owned |
| `average_buy_price` | `Float` | No | — | Weighted average purchase price across all buys |
| `updated_at` | `DateTime` | No | `utcnow` | Last modification time |

**Indexes:** `user_id`

---

### `trades`

Immutable log of every buy and sell transaction, including bankruptcy liquidation sells.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `user_id` | `Integer` | No | — | FK → `users.id` |
| `ticker` | `String` | No | — | Stock symbol |
| `trade_type` | `String` | No | — | `"buy"` or `"sell"` |
| `quantity` | `Integer` | No | — | Number of shares traded |
| `price` | `Float` | No | — | Price per share at execution time |
| `total_value` | `Float` | No | — | `price × quantity` |
| `timestamp` | `DateTime` | No | `utcnow` | When the trade was executed |

**Indexes:** `user_id`

---

### `auto_trades`

Pending conditional trading rules. Executed by the background scheduler when `target_price` is reached.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `user_id` | `Integer` | No | — | FK → `users.id` |
| `ticker` | `String` | No | — | Stock symbol |
| `trade_type` | `String` | No | — | `"buy"` or `"sell"` |
| `target_price` | `Float` | No | — | Price that triggers execution |
| `quantity` | `Integer` | No | — | Number of shares to trade |
| `is_active` | `Boolean` | No | `true` | `false` after execution, cancellation, or bankruptcy |
| `created_at` | `DateTime` | No | `utcnow` | Rule creation time |

**Execution logic:**
- `buy` → executes when `current_price <= target_price`
- `sell` → executes when `current_price >= target_price`

---

### `stock_price_history`

Time-series of fetched stock prices. Written by the price polling service. Used to serve current prices from cache/DB when the external API is unavailable.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `ticker` | `String` | No | — | Stock symbol |
| `price` | `Float` | No | — | Price in USD at the recorded time |
| `timestamp` | `DateTime` | No | `utcnow` | When the price was recorded |

**Indexes:** `ticker`

---

### `net_worth_history`

Daily snapshots of each user's total net worth (cash + holdings market value). Written by the daily snapshot task. Used for the leaderboard history chart.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` | No | auto | Primary key |
| `user_id` | `Integer` | No | — | FK → `users.id` |
| `net_worth` | `Float` | No | — | Cash balance + market value of all holdings at snapshot time |
| `timestamp` | `DateTime` | No | `utcnow` | When the snapshot was taken |

**Indexes:** `user_id`

Bankrupt users are skipped during snapshotting.

---

## Entity Relationships


users
 ├── holdings        (user_id → users.id)
 ├── trades          (user_id → users.id)
 ├── auto_trades     (user_id → users.id)
 └── net_worth_history (user_id → users.id)

stock_price_history 

---

## Migrations

Migrations live in `backend/alembic/versions/`. Run with:

```bash
alembic upgrade head
```

| Revision | Description |
|----------|-------------|
| `5468d9510b3b` | Initial schema |
| `c9b9ec50f5b4` | Add `username` to `users` |
| `a1b2c3d4e5f6` | Add `bankrupt_at` to `users` |
