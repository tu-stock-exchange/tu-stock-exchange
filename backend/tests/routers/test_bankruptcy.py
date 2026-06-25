import pytest
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
from datetime import datetime

from main import app
from app.core.auth_dependencies import get_current_user
from app.models.holding import Holding
from app.models.auto_trade import AutoTrade
from app.models.trade import Trade
from app.models.users import User


def make_fake_user(**kwargs):
    defaults = dict(
        id=1,
        email="test@test.com",
        balance=10000.0,
        is_bankrupt=False,
        bankrupt_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)

# service: check_and_handle_bankruptcy

class TestCheckAndHandleBankruptcy:

    @pytest.mark.asyncio
    async def test_no_bankruptcy_above_threshold(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u@test.com", password_hash="x", balance=5000.0, is_bankrupt=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        went_bankrupt = await check_and_handle_bankruptcy(user, 5000.0, db)

        assert went_bankrupt is False
        assert user.is_bankrupt is False
        assert user.bankrupt_at is None

    @pytest.mark.asyncio
    async def test_bankruptcy_triggered_below_threshold(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u2@test.com", password_hash="x", balance=50.0, is_bankrupt=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        with patch(
            "app.services.default_services.get_current_price",
            new=AsyncMock(return_value=10.0),
        ):
            went_bankrupt = await check_and_handle_bankruptcy(user, 50.0, db)

        assert went_bankrupt is True
        assert user.is_bankrupt is True
        assert user.bankrupt_at is not None

    @pytest.mark.asyncio
    async def test_holdings_liquidated_on_bankruptcy(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u3@test.com", password_hash="x", balance=10.0, is_bankrupt=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        holding = Holding(
            user_id=user.id, ticker="AAPL", quantity=1, average_buy_price=5.0
        )
        db.add(holding)
        db.commit()

        with patch(
            "app.services.default_services.get_current_price",
            new=AsyncMock(return_value=5.0),
        ):
            await check_and_handle_bankruptcy(user, 15.0, db)

        remaining = db.query(Holding).filter(Holding.user_id == user.id).all()
        assert remaining == []

        sell_trades = (
            db.query(Trade)
            .filter(Trade.user_id == user.id, Trade.trade_type == "sell")
            .all()
        )
        assert len(sell_trades) == 1
        assert sell_trades[0].ticker == "AAPL"

    @pytest.mark.asyncio
    async def test_auto_trades_cancelled_on_bankruptcy(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u4@test.com", password_hash="x", balance=10.0, is_bankrupt=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        auto_trade = AutoTrade(
            user_id=user.id,
            ticker="AAPL",
            trade_type="buy",
            target_price=100.0,
            quantity=1,
            is_active=True,
        )
        db.add(auto_trade)
        db.commit()

        with patch(
            "app.services.default_services.get_current_price",
            new=AsyncMock(return_value=5.0),
        ):
            await check_and_handle_bankruptcy(user, 10.0, db)

        db.refresh(auto_trade)
        assert auto_trade.is_active is False

    @pytest.mark.asyncio
    async def test_already_bankrupt_user_skipped(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u5@test.com",
            password_hash="x",
            balance=10.0,
            is_bankrupt=True,
            bankrupt_at=datetime(2026, 1, 1),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        went_bankrupt = await check_and_handle_bankruptcy(user, 10.0, db)

        assert went_bankrupt is False
        assert user.bankrupt_at == datetime(2026, 1, 1)

    @pytest.mark.asyncio
    async def test_liquidation_uses_fallback_price_when_api_fails(self, db):
        from app.services.default_services import check_and_handle_bankruptcy

        user = User(
            email="u6@test.com", password_hash="x", balance=10.0, is_bankrupt=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        holding = Holding(
            user_id=user.id, ticker="AAPL", quantity=2, average_buy_price=20.0
        )
        db.add(holding)
        db.commit()
        balance_before = user.balance

        with patch(
            "app.services.default_services.get_current_price",
            new=AsyncMock(return_value=None),
        ):
            await check_and_handle_bankruptcy(user, 10.0, db)

        assert user.balance == balance_before + 2 * 20.0


# service: recover_from_bankruptcy

class TestRecoverFromBankruptcy:

    def test_recovery_resets_balance(self, db):
        from app.services.default_services import recover_from_bankruptcy, RECOVERY_BALANCE

        user = User(
            email="r1@test.com",
            password_hash="x",
            balance=50.0,
            is_bankrupt=True,
            bankrupt_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        recover_from_bankruptcy(user, db)

        assert user.is_bankrupt is False
        assert user.balance == RECOVERY_BALANCE

    def test_recovery_preserves_bankrupt_at(self, db):
        from app.services.default_services import recover_from_bankruptcy

        bankrupt_time = datetime(2026, 5, 1)
        user = User(
            email="r2@test.com",
            password_hash="x",
            balance=50.0,
            is_bankrupt=True,
            bankrupt_at=bankrupt_time,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        recover_from_bankruptcy(user, db)

        assert user.bankrupt_at == bankrupt_time

    def test_recovery_noop_for_healthy_user(self, db):
        from app.services.default_services import recover_from_bankruptcy

        user = User(
            email="r3@test.com",
            password_hash="x",
            balance=5000.0,
            is_bankrupt=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        recover_from_bankruptcy(user, db)

        assert user.balance == 5000.0
        assert user.is_bankrupt is False

# router: POST /users/me/recover

class TestRecoverEndpoint:

    def test_recover_endpoint_success(self, client):
        from app.services.default_services import RECOVERY_BALANCE

        fake_user = make_fake_user(balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        app.dependency_overrides[get_current_user] = lambda: fake_user

        with patch("app.routers.users.recover_from_bankruptcy") as mock_recover:
            mock_recover.return_value = SimpleNamespace(
                id=1,
                email="test@test.com",
                balance=RECOVERY_BALANCE,
                is_bankrupt=False,
                bankrupt_at=fake_user.bankrupt_at,
                registered_at=datetime.utcnow(),
            )
            response = client.post("/api/users/me/recover")

        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["is_bankrupt"] is False
        assert data["balance"] == RECOVERY_BALANCE

    def test_recover_endpoint_not_bankrupt(self, client):
        fake_user = make_fake_user()
        app.dependency_overrides[get_current_user] = lambda: fake_user

        response = client.post("/api/users/me/recover")
        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 400
        assert "not bankrupt" in response.json()["detail"]


# router: trading — bankruptcy check triggered after trades

class TestBankruptcyTriggeredByTrade:

    def test_buy_triggers_bankruptcy_when_net_worth_drops(self, client, db):
        fake_user = make_fake_user(balance=60.0)
        app.dependency_overrides[get_current_user] = lambda: fake_user

        with patch("app.routers.trading.get_current_price", return_value=55.0), \
             patch(
                 "app.routers.trading.check_and_handle_bankruptcy",
                 new=AsyncMock(return_value=True),
             ) as mock_check:
            response = client.post(
                "/api/trades/buy", json={"ticker": "AAPL", "quantity": 1}
            )

        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        mock_check.assert_called_once()

    def test_sell_triggers_bankruptcy_check(self, client, db):
        fake_user = make_fake_user(balance=10.0)
        app.dependency_overrides[get_current_user] = lambda: fake_user

        holding = Holding(
            user_id=1, ticker="AAPL", quantity=5, average_buy_price=10.0
        )
        db.add(holding)
        db.commit()

        with patch("app.routers.trading.get_current_price", return_value=5.0), \
             patch(
                 "app.routers.trading.check_and_handle_bankruptcy",
                 new=AsyncMock(return_value=False),
             ) as mock_check:
            response = client.post(
                "/api/trades/sell", json={"ticker": "AAPL", "quantity": 5}
            )

        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        mock_check.assert_called_once()

    def test_bankrupt_user_cannot_buy(self, client):
        fake_user = make_fake_user(is_bankrupt=True)
        app.dependency_overrides[get_current_user] = lambda: fake_user

        response = client.post(
            "/api/trades/buy", json={"ticker": "AAPL", "quantity": 1}
        )
        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 403
        assert response.json()["detail"] == "Account is bankrupt"

    def test_bankrupt_user_cannot_sell(self, client):
        fake_user = make_fake_user(is_bankrupt=True)
        app.dependency_overrides[get_current_user] = lambda: fake_user

        response = client.post(
            "/api/trades/sell", json={"ticker": "AAPL", "quantity": 1}
        )
        app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 403
        assert response.json()["detail"] == "Account is bankrupt"
