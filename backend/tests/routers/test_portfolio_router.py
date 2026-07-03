from datetime import datetime, timedelta

from app.models.users import User
from app.models.net_worth_history import NetWorthHistory
from app.models.holding_history import HoldingHistory


def create_user(db, **kwargs):
    defaults = dict(email="portfolio@test.com", password_hash="x", balance=10000.0)
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestGetPortfolioHistory:
    """Tests for GET /api/users/{user_id}/portfolio/history"""

    def test_user_not_found_returns_404(self, client):
        response = client.get("/api/users/9999/portfolio/history")

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_no_history_returns_empty_list(self, client, db):
        user = create_user(db)

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        assert response.json() == []

    def test_snapshot_without_holdings(self, client, db):
        user = create_user(db)
        timestamp = datetime(2024, 1, 1, 12, 0, 0)

        db.add(NetWorthHistory(user_id=user.id, net_worth=10000.0, timestamp=timestamp))
        db.commit()

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        entry = data[0]
        assert entry["net_worth"] == 10000.0
        assert entry["balance"] == 10000.0
        assert entry["holdings_value"] == 0.0
        assert entry["holdings"] == []

    def test_snapshot_with_holdings(self, client, db):
        user = create_user(db)
        timestamp = datetime(2024, 1, 2, 12, 0, 0)

        db.add(NetWorthHistory(user_id=user.id, net_worth=11500.0, timestamp=timestamp))
        db.add(
            HoldingHistory(
                user_id=user.id,
                ticker="AAPL",
                quantity=10,
                average_buy_price=140.0,
                current_price=150.0,
                timestamp=timestamp,
            )
        )
        db.commit()

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        entry = data[0]

        # holdings_value = 10 * 150.0 = 1500.0; balance = net_worth - holdings_value
        assert entry["net_worth"] == 11500.0
        assert entry["holdings_value"] == 1500.0
        assert entry["balance"] == 10000.0
        assert len(entry["holdings"]) == 1
        holding = entry["holdings"][0]
        assert holding["ticker"] == "AAPL"
        assert holding["quantity"] == 10
        assert holding["average_buy_price"] == 140.0
        assert holding["current_price"] == 150.0

    def test_snapshot_with_multiple_holdings(self, client, db):
        user = create_user(db)
        timestamp = datetime(2024, 1, 3, 12, 0, 0)

        db.add(NetWorthHistory(user_id=user.id, net_worth=13000.0, timestamp=timestamp))
        db.add(
            HoldingHistory(
                user_id=user.id, ticker="AAPL", quantity=10,
                average_buy_price=140.0, current_price=150.0, timestamp=timestamp,
            )
        )
        db.add(
            HoldingHistory(
                user_id=user.id, ticker="TSLA", quantity=5,
                average_buy_price=200.0, current_price=250.0, timestamp=timestamp,
            )
        )
        db.commit()

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        data = response.json()
        entry = data[0]

        # holdings_value = (10 * 150.0) + (5 * 250.0) = 1500.0 + 1250.0 = 2750.0
        assert entry["holdings_value"] == 2750.0
        assert entry["balance"] == 10250.0
        tickers = {h["ticker"] for h in entry["holdings"]}
        assert tickers == {"AAPL", "TSLA"}

    def test_multiple_snapshots_ordered_chronologically(self, client, db):
        user = create_user(db)
        day1 = datetime(2024, 1, 1, 12, 0, 0)
        day2 = datetime(2024, 1, 2, 12, 0, 0)

        # Insert out of order to verify the endpoint orders by timestamp
        db.add(NetWorthHistory(user_id=user.id, net_worth=12000.0, timestamp=day2))
        db.add(NetWorthHistory(user_id=user.id, net_worth=10000.0, timestamp=day1))
        db.commit()

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["timestamp"] == day1.isoformat()
        assert data[0]["net_worth"] == 10000.0
        assert data[1]["timestamp"] == day2.isoformat()
        assert data[1]["net_worth"] == 12000.0

    def test_holdings_from_different_timestamp_not_included(self, client, db):
        user = create_user(db)
        snapshot_time = datetime(2024, 1, 5, 12, 0, 0)
        other_time = datetime(2024, 1, 4, 12, 0, 0)

        db.add(NetWorthHistory(user_id=user.id, net_worth=10000.0, timestamp=snapshot_time))
        db.add(
            HoldingHistory(
                user_id=user.id, ticker="AAPL", quantity=10,
                average_buy_price=140.0, current_price=150.0, timestamp=other_time,
            )
        )
        db.commit()

        response = client.get(f"/api/users/{user.id}/portfolio/history")

        assert response.status_code == 200
        entry = response.json()[0]
        assert entry["holdings"] == []
        assert entry["holdings_value"] == 0.0
        assert entry["balance"] == 10000.0

    def test_history_scoped_to_requested_user(self, client, db):
        user1 = create_user(db, email="user1@test.com")
        user2 = create_user(db, email="user2@test.com")
        timestamp = datetime(2024, 1, 6, 12, 0, 0)

        db.add(NetWorthHistory(user_id=user1.id, net_worth=10000.0, timestamp=timestamp))
        db.add(NetWorthHistory(user_id=user2.id, net_worth=20000.0, timestamp=timestamp))
        db.commit()

        response = client.get(f"/api/users/{user1.id}/portfolio/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["net_worth"] == 10000.0