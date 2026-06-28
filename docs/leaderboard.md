# Leaderboard

## Endpoints

Two endpoints exist, both public (no authentication required).

- `GET /api/leaderboard` — live standings right now
- `GET /api/leaderboard/history?days=30` — historical snapshots over time

---

## Live leaderboard

`GET /api/leaderboard` calculates each user's portfolio value on the fly and returns the top 5.

**Calculation**

```
portfolio_value = user.balance + sum(holding.quantity × current_price for each holding)
```

All unique tickers across all holdings are fetched from `get_current_price` first, deduplicating API calls. If a price is unavailable the ticker contributes `0.0` to the total rather than raising an error. Results are sorted descending by `portfolio_value` and capped at 5 entries.

**Response**

```json
[
  { "user_id": 3, "username": "alice", "portfolio_value": 14250.00 },
  { "user_id": 7, "username": "bob",   "portfolio_value": 12800.50 }
]
```

| Field | Description |
|---|---|
| `user_id` | User's primary key |
| `username` | Display name |
| `portfolio_value` | Cash + holdings value, rounded to 2 dp |

---

## Leaderboard history

`GET /api/leaderboard/history` replays rankings over time from the `net_worth_history` table, which is populated once per day by the snapshot task.

**Query parameter**

| Parameter | Default | Description |
|---|---|---|
| `days` | `30` | How many days back to include |

**How rankings are built**

For each distinct timestamp present in `net_worth_history` within the requested window:

1. All user records at that timestamp are sorted descending by `net_worth`.
2. Each user is assigned a `rank` starting at 1.
3. Up to the top 10 users are included per timestamp.
4. Usernames are resolved by a per-user `User` query inside the loop.

Results are returned in ascending timestamp order (oldest first).

**Response**

```json
[
  {
    "timestamp": "2024-01-01T00:00:00",
    "rankings": [
      { "user_id": 3, "username": "alice", "portfolio_value": 13000.00, "rank": 1 },
      { "user_id": 7, "username": "bob",   "portfolio_value": 11500.00, "rank": 2 }
    ]
  },
  {
    "timestamp": "2024-01-02T00:00:00",
    "rankings": [
      { "user_id": 7, "username": "bob",   "portfolio_value": 14000.00, "rank": 1 },
      { "user_id": 3, "username": "alice", "portfolio_value": 13200.00, "rank": 2 }
    ]
  }
]
```

The `rank` field is additive on top of `LeaderboardItem` — it exists only in the history response, not the live leaderboard response.

**Performance note** — the history endpoint does one `User` query per record inside the timestamp loop. For large datasets this should be replaced with a single join or an in-memory user map built before the loop.

---

## Data source for history

The `net_worth_history` table is written by `app/tasks/snapshot.py`, which runs daily at 00:00 UTC via APScheduler. Each run writes one row per active (non-bankrupt) user. Bankrupt users are excluded from snapshots and therefore absent from historical rankings.

The `net_worth` value stored is `user.balance + sum(holding.quantity × live_price)`, calculated at snapshot time. It reflects market prices at midnight UTC, not at trade time.
