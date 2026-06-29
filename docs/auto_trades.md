# Auto Trades

## Creating auto trades

`POST /api/auto-trades` accepts `{ ticker, trade_type, target_price, quantity }`.

1. Creates a new `AutoTrade` row in the database with `is_active = True`.
2. The trade does **not** execute immediately — it waits until the target price is reached.
3. `trade_type` must be `"buy"` or `"sell"`.

Response fields: `message`, `id`.

## Deleting auto trades

`DELETE /api/auto-trades/{auto_trade_id}` deactivates an auto trade.

1. Looks up the auto trade by `id` and `user_id` (users can only delete their own).
2. Returns 404 if the auto trade does not exist.
3. Sets `is_active = False` — the row stays in the database (soft delete).

Response fields: `message`.

## Execution rules

`check_auto_trades()` runs every hour via the APScheduler background scheduler.

1. Fetches all auto trades where `is_active = True`.
2. For each trade, fetches the current market price of the ticker.
3. Executes if the price condition is met:
   - `buy` — executes when `current_price <= target_price`
   - `sell` — executes when `current_price >= target_price`
4. On execution: updates the user's balance, updates holdings, creates a `Trade` record, sets `is_active = False`.
5. Skips the trade if the user is bankrupt or has insufficient funds for a buy.

## Invalid ticker behavior

If `get_current_price(ticker)` returns `None` (unknown or unavailable ticker):

- The executor skips the trade silently and moves to the next one.
- The auto trade stays `is_active = True` and will be retried on the next hourly run.
- No error is raised and no notification is sent to the user.
