# Portfolio

## Portfolio calculation

Net worth is always computed live, never stored on the user row. The formula is:

```
net_worth = user.balance + sum(holding.quantity × current_price for each holding)
```

`current_price` is fetched from `get_current_price(ticker)`, which checks Redis first (1-hour TTL) before hitting Finnhub. If the price API is unavailable the calculation falls back to `holding.average_buy_price` so the endpoint never returns an error during market closures or API outages.

The daily snapshot task (`app/tasks/snapshot.py`) persists net worth into `net_worth_history` and each holding's state into `holding_history`. Those tables power the portfolio history endpoint; the live portfolio endpoint always reflects the current moment.

## Portfolio endpoint response

`GET /api/portfolio` returns the current state of the authenticated user's portfolio.

```json
{
  "holdings": [
    {
      "ticker": "AAPL",
      "quantity": 10,
      "average_buy_price": 140.0,
      "current_price": 155.0,
      "current_value": 1550.0,
      "cost_basis": 1400.0,
      "pnl": 150.0,
      "pnl_percent": 10.71
    }
  ],
  "total_current_value": 1550.0,
  "total_cost_basis": 1400.0,
  "total_pnl": 150.0,
  "cash_balance": 8450.0
}
```

Field definitions:

| Field | Formula |
|---|---|
| `current_value` | `quantity × current_price` |
| `cost_basis` | `quantity × average_buy_price` |
| `pnl` | `current_value − cost_basis` |
| `pnl_percent` | `(pnl / cost_basis) × 100` |
| `total_current_value` | sum of all `current_value` |
| `total_cost_basis` | sum of all `cost_basis` |
| `total_pnl` | `total_current_value − total_cost_basis` |
| `cash_balance` | `user.balance` |

All monetary values are rounded to 2 decimal places. `pnl_percent` is 0.0 when `cost_basis` is zero.

## Related endpoints

`GET /api/portfolio/networth` returns a condensed summary without the per-holding breakdown:

```json
{
  "networth": 10000.0,
  "cash_balance": 8450.0,
  "total_stock_value": 1550.0
}
```

`GET /api/users/{user_id}/portfolio/history` returns the time-series of daily snapshots from `net_worth_history` joined to `holding_history` by timestamp. See `app/routers/portfolio.py`.
