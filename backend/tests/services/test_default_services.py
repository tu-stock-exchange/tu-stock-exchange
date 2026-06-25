import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.models.auto_trade import AutoTrade
from app.models.holding import Holding
from app.models.trade import Trade
from app.models.users import User
from app.services.default_services import (
    BANKRUPTCY_THRESHOLD,
    RECOVERY_BALANCE,
    check_and_handle_bankruptcy,
    recover_from_bankruptcy,
)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def make_user(db, email, balance=10000.0, is_bankrupt=False, bankrupt_at=None):
    user = User(
        email=email,
        password_hash="x",
        balance=balance,
        is_bankrupt=is_bankrupt,
        bankrupt_at=bankrupt_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# check_and_handle_bankruptcy


class TestCheckAndHandleBankruptcy:

    def test_no_action_when_net_worth_above_threshold(self, db):
        user = make_user(db, "a1@t.com", balance=500.0)
        went_bankrupt = run(check_and_handle_bankruptcy(user, 500.0, db))
        assert went_bankrupt is False
        assert user.is_bankrupt is False

    def test_no_action_when_net_worth_equals_threshold(self, db):
        user = make_user(db, "a2@t.com", balance=BANKRUPTCY_THRESHOLD)
        went_bankrupt = run(check_and_handle_bankruptcy(user, BANKRUPTCY_THRESHOLD, db))
        assert went_bankrupt is False
        assert user.is_bankrupt is False

    def test_bankruptcy_triggered_one_cent_below_threshold(self, db):
        net_worth = BANKRUPTCY_THRESHOLD - 0.01
        user = make_user(db, "a3@t.com", balance=net_worth)
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            went_bankrupt = run(check_and_handle_bankruptcy(user, net_worth, db))
        assert went_bankrupt is True

    def test_is_bankrupt_set_to_true(self, db):
        user = make_user(db, "a4@t.com", balance=50.0)
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            run(check_and_handle_bankruptcy(user, 50.0, db))
        assert user.is_bankrupt is True

    def test_bankrupt_at_timestamp_set(self, db):
        user = make_user(db, "a5@t.com", balance=50.0)
        before = datetime.utcnow()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            run(check_and_handle_bankruptcy(user, 50.0, db))
        assert user.bankrupt_at is not None
        assert user.bankrupt_at >= before

    def test_already_bankrupt_user_is_skipped(self, db):
        original_ts = datetime(2026, 1, 1)
        user = make_user(db, "a6@t.com", balance=10.0, is_bankrupt=True, bankrupt_at=original_ts)
        went_bankrupt = run(check_and_handle_bankruptcy(user, 10.0, db))
        assert went_bankrupt is False
        assert user.bankrupt_at == original_ts

    def test_holding_deleted_on_bankruptcy(self, db):
        user = make_user(db, "a7@t.com", balance=10.0)
        db.add(Holding(user_id=user.id, ticker="AAPL", quantity=1, average_buy_price=5.0))
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=5.0)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        assert db.query(Holding).filter(Holding.user_id == user.id).count() == 0

    def test_sell_trade_created_for_each_holding(self, db):
        user = make_user(db, "a8@t.com", balance=10.0)
        for ticker in ("AAPL", "TSLA", "GOOG"):
            db.add(Holding(user_id=user.id, ticker=ticker, quantity=2, average_buy_price=5.0))
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=5.0)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        sell_trades = (
            db.query(Trade)
            .filter(Trade.user_id == user.id, Trade.trade_type == "sell")
            .all()
        )
        assert len(sell_trades) == 3

    def test_liquidation_value_added_to_balance(self, db):
        user = make_user(db, "a9@t.com", balance=10.0)
        db.add(Holding(user_id=user.id, ticker="AAPL", quantity=3, average_buy_price=0.0))
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=5.0)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        # balance = 10 + 3*5 = 25
        assert user.balance == 10.0 + 3 * 5.0

    def test_fallback_to_average_buy_price_when_api_fails(self, db):
        user = make_user(db, "a10@t.com", balance=10.0)
        db.add(Holding(user_id=user.id, ticker="AAPL", quantity=2, average_buy_price=20.0))
        db.commit()
        balance_before = user.balance
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        assert user.balance == balance_before + 2 * 20.0

    def test_active_auto_trades_cancelled(self, db):
        user = make_user(db, "a11@t.com", balance=10.0)
        at = AutoTrade(
            user_id=user.id, ticker="AAPL", trade_type="buy",
            target_price=100.0, quantity=1, is_active=True,
        )
        db.add(at)
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        db.refresh(at)
        assert at.is_active is False

    def test_inactive_auto_trades_unchanged(self, db):
        user = make_user(db, "a12@t.com", balance=10.0)
        at = AutoTrade(
            user_id=user.id, ticker="AAPL", trade_type="buy",
            target_price=100.0, quantity=1, is_active=False,
        )
        db.add(at)
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=None)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        db.refresh(at)
        assert at.is_active is False

    def test_user_with_no_holdings_goes_bankrupt(self, db):
        user = make_user(db, "a13@t.com", balance=50.0)
        went_bankrupt = run(check_and_handle_bankruptcy(user, 50.0, db))
        assert went_bankrupt is True
        assert user.is_bankrupt is True

    def test_sell_trade_records_correct_quantity_and_price(self, db):
        user = make_user(db, "a14@t.com", balance=10.0)
        db.add(Holding(user_id=user.id, ticker="AAPL", quantity=7, average_buy_price=0.0))
        db.commit()
        with patch("app.services.default_services.get_current_price", new=AsyncMock(return_value=3.0)):
            run(check_and_handle_bankruptcy(user, 10.0, db))
        trade = db.query(Trade).filter(Trade.user_id == user.id).first()
        assert trade.quantity == 7
        assert trade.price == 3.0
        assert trade.total_value == 21.0

# recover_from_bankruptcy


class TestRecoverFromBankruptcy:

    def test_balance_reset_to_recovery_balance(self, db):
        user = make_user(db, "r1@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        recover_from_bankruptcy(user, db)
        assert user.balance == RECOVERY_BALANCE

    def test_is_bankrupt_cleared(self, db):
        user = make_user(db, "r2@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        recover_from_bankruptcy(user, db)
        assert user.is_bankrupt is False

    def test_bankrupt_at_preserved_after_recovery(self, db):
        ts = datetime(2026, 3, 15, 12, 0, 0)
        user = make_user(db, "r3@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=ts)
        recover_from_bankruptcy(user, db)
        assert user.bankrupt_at == ts

    def test_recovery_is_noop_for_healthy_user(self, db):
        user = make_user(db, "r4@t.com", balance=5000.0, is_bankrupt=False)
        recover_from_bankruptcy(user, db)
        assert user.balance == 5000.0
        assert user.is_bankrupt is False

    def test_recovery_returns_user_object(self, db):
        user = make_user(db, "r5@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        result = recover_from_bankruptcy(user, db)
        assert result is user

    def test_recovery_balance_persisted_in_db(self, db):
        user = make_user(db, "r6@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        recover_from_bankruptcy(user, db)
        db.expire(user)
        db.refresh(user)
        assert user.balance == RECOVERY_BALANCE
        assert user.is_bankrupt is False

    def test_double_recovery_is_noop(self, db):
        user = make_user(db, "r7@t.com", balance=50.0, is_bankrupt=True, bankrupt_at=datetime.utcnow())
        recover_from_bankruptcy(user, db)
        balance_after_first = user.balance
        recover_from_bankruptcy(user, db)
        assert user.balance == balance_after_first
