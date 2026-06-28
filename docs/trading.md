# Trading

## Buy logic

`POST /api/trades/buy` accepts `{ ticker, quantity }`.

1. Reject if the account is bankrupt (403).
2. Reject if `quantity <= 0` (400).
3. Fetch the live price via `get_current_price(ticker)`. Reject with 503 if unavailable.
4. Compute `total_cost = price × quantity` (rounded to 2 dp).
5. Reject if `user.balance < total_cost` — see [Insufficient funds](#insufficient-funds).
6. Deduct `total_cost` from `user.balance`.
7. Append a `Trade` row (`trade_type="buy"`).
8. Update holdings — see [Holdings updates](#holdings-updates).
9. Commit, then run the bankruptcy check against the settled net worth.

Response fields: `ticker`, `quantity`, `price_per_stock`, `total_cost`, `new_balance`.

## Sell logic

`POST /api/trades/sell` accepts `{ ticker, quantity }`.

1. Reject if the account is bankrupt (403).
2. Reject if `quantity <= 0` (400).
3. Look up the holding. Reject if it doesn't exist or `holding.quantity < quantity` — see [Selling more shares than owned](#selling-more-shares-than-owned).
4. Fetch the live price. Reject with 503 if unavailable.
5. Compute `total_value = price × quantity` (rounded to 2 dp).
6. Add `total_value` to `user.balance`.
7. Append a `Trade` row (`trade_type="sell"`).
8. Reduce the holding — see [Holdings updates](#holdings-updates).
9. Commit, then run the bankruptcy check against the settled net worth.

Response fields: `ticker`, `quantity`, `price_per_stock`, `total_value`, `new_balance`.

## Holdings updates

The `holdings` table stores one row per `(user_id, ticker)` pair representing the current live position.

**On buy** — if a holding already exists, the average buy price is recalculated as a weighted average:

```
new_avg = (old_quantity × old_avg + buy_quantity × buy_price) / (old_quantity + buy_quantity)
```

`quantity` is incremented and `updated_at` is refreshed. If no holding exists, a new row is inserted with `average_buy_price = buy_price`.

**On sell** — `quantity` is decremented. When it reaches zero the row is deleted. `average_buy_price` is never modified on a sell; it is a cost-basis field, not a running average.

## Insufficient funds

Checked before any state is mutated. The comparison uses the rounded `total_cost` value to avoid floating-point false rejections (e.g. `150.0 × 3` can produce `449.9999…` in IEEE 754). Returns 400:

```
Insufficient funds. Need $<total_cost>, have $<balance>
```

## Selling more shares than owned

Checked before fetching the price. Returns 400 in two cases:

- No holding row exists for the ticker (user owns 0 shares).
- `holding.quantity < requested quantity`.

```
Not enough stocks. You have <N> share(s) of <TICKER>
```

The ticker is included in the message so the client can surface it directly without inspecting the request body.
