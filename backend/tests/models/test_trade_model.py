from datetime import datetime

from app.models.trade import Trade
from app.models.users import User


class TestTradeModel:
    """Unit tests for the Trade SQLAlchemy model."""

    def test_create_buy_trade(self, db):
        """A buy trade can be created and persisted with all its fields."""
        user = User(email="trader@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        trade = Trade(
            user_id=user.id,
            ticker="AAPL",
            trade_type="buy",
            quantity=5,
            price=150.0,
            total_value=750.0,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        assert trade.id is not None
        assert trade.user_id == user.id
        assert trade.ticker == "AAPL"
        assert trade.trade_type == "buy"
        assert trade.quantity == 5
        assert trade.price == 150.0
        assert trade.total_value == 750.0

    def test_create_sell_trade(self, db):
        """A sell trade can be created and persisted."""
        user = User(email="trader2@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        trade = Trade(
            user_id=user.id,
            ticker="TSLA",
            trade_type="sell",
            quantity=2,
            price=200.0,
            total_value=400.0,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        assert trade.trade_type == "sell"
        assert trade.total_value == 400.0

    def test_timestamp_defaults_to_now(self, db):
        """timestamp is populated automatically when not supplied."""
        user = User(email="trader3@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        before = datetime.utcnow()
        trade = Trade(
            user_id=user.id,
            ticker="MSFT",
            trade_type="buy",
            quantity=1,
            price=300.0,
            total_value=300.0,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        after = datetime.utcnow()

        assert trade.timestamp is not None
        assert before <= trade.timestamp <= after

    def test_tablename(self):
        """The model maps to the 'trades' table."""
        assert Trade.__tablename__ == "trades"

    def test_multiple_trades_per_user(self, db):
        """A user can have many trade records."""
        user = User(email="trader4@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        trade1 = Trade(user_id=user.id, ticker="AAPL", trade_type="buy", quantity=5, price=150.0, total_value=750.0)
        trade2 = Trade(user_id=user.id, ticker="TSLA", trade_type="sell", quantity=2, price=200.0, total_value=400.0)
        db.add_all([trade1, trade2])
        db.commit()

        trades = db.query(Trade).filter(Trade.user_id == user.id).all()
        assert len(trades) == 2

    def test_query_orders_by_timestamp(self, db):
        """Trades can be queried and ordered by their timestamp."""
        user = User(email="trader5@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        older = Trade(
            user_id=user.id, ticker="AAPL", trade_type="buy", quantity=1,
            price=100.0, total_value=100.0, timestamp=datetime(2020, 1, 1),
        )
        newer = Trade(
            user_id=user.id, ticker="AAPL", trade_type="sell", quantity=1,
            price=110.0, total_value=110.0, timestamp=datetime(2021, 1, 1),
        )
        db.add_all([newer, older])
        db.commit()

        ordered = db.query(Trade).filter(Trade.user_id == user.id).order_by(Trade.timestamp).all()