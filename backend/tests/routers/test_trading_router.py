import pytest
from unittest.mock import patch
from types import SimpleNamespace
from main import app
from app.core.auth_dependencies import get_current_user

def make_fake_user():
    return SimpleNamespace(
        id=1,
        email="test@test.com",
        balance=10000.0,
        is_bankrupt=False
    )

def test_buy_stock_success(client):
    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda: fake_user

    with patch("app.routers.trading.get_current_price", return_value=150.0):
        response = client.post(
            "/api/trades/buy",
            json={"ticker": "AAPL", "quantity": 1}
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["quantity"] == 1
    assert "total_cost" in data
    assert "new_balance" in data

def test_buy_stock_insufficient_funds(client): 
    fake_user = make_fake_user()
    fake_user.balance = 100.0
    
    app.dependency_overrides[get_current_user] = lambda : fake_user

    with patch("app.routers.trading.get_current_price", return_value = 150.0):
        response = client.post(
            "/api/trades/buy", 
            json = {'ticker' : 'AAPL', 'quantity' : 10}
        )

    app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


def test_user_is_bankrupt(client):

    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda : fake_user

    fake_user.is_bankrupt = True

    response = client.post(
        "api/trades/buy", 
        json = {"ticker" : "AAPL", "quantity" : 3}
    )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is bankrupt"

def test_sell_stock_success(client, db): 

    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda : fake_user

    from app.models.holding import Holding

    holding = Holding(
        user_id = 1, 
        ticker = "AAPL", 
        quantity = 10, 
        average_buy_price = 140.0
    )

    db.add(holding)
    db.commit()

    with patch("app.routers.trading.get_current_price", return_value = 150.0):
        response = client.post(
            "/api/trades/sell", 
            json = {"ticker" : "AAPL", "quantity" : 5}
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["quantity"] == 5
    assert "new_balance" in data
def test_sell_stock_not_enough(client):
    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda: fake_user

    with patch("app.routers.trading.get_current_price", return_value=150.0):
        response = client.post(
            "/api/trades/sell",
            json={"ticker": "AAPL", "quantity": 5}
        )

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 400
    assert "Not enough stocks" in response.json()["detail"]

def test_get_portfolio_empty(client):

    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda : fake_user

    response = client.get("/api/portfolio")

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert data["holdings"] == []
    assert data["total_current_value"] == 0.0
    assert data["cash_balance"] == 10000.0 

def test_get_portfolio_with_holdings(client, db): 

    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda : fake_user

    from app.models.holding import Holding

    holding1 = Holding(
        user_id = 1, 
        ticker = "AAPL", 
        quantity = 10, 
        average_buy_price = 140.0
    )

    db.add(holding1)
    db.commit()

    with patch("app.routers.trading.get_current_price", return_value = 150.0):
        response = client.get("api/portfolio")

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert len(data["holdings"]) == 1
    assert data["holdings"][0]["ticker"] == "AAPL"
    assert data["holdings"][0]["quantity"] == 10
    assert data["holdings"][0]["pnl"] == 100.0

def test_get_trade_history(client, db): 

    fake_user = make_fake_user()
    app.dependency_overrides[get_current_user] = lambda : fake_user

    from app.models.trade import Trade

    trade1 = Trade(user_id=1, ticker="AAPL", trade_type="buy", quantity=5, price=150.0, total_value=750.0)
    trade2 = Trade(user_id=1, ticker="TSLA", trade_type="sell", quantity=2, price=200.0, total_value=400.0)
    db.add(trade1)
    db.add(trade2)
    db.commit()

    response = client.get("/api/trades/history")

    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    data = response.json()
    assert len(data["trades"]) == 2
    assert data["page"] == 1