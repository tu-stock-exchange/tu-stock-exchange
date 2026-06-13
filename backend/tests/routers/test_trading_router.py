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
