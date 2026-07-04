from datetime import datetime

from app.models.holding import Holding
from app.models.users import User


class TestHoldingModel:
    """Unit tests for the Holding SQLAlchemy model."""

    def test_create_holding(self, db):
        """A holding can be created and persisted with all its fields."""
        user = User(email="holder@test.com", password_hash="x", balance=10000.0)
        db.add(user)
        db.commit()
        db.refresh(user)

        holding = Holding(
            user_id=user.id,
            ticker="AAPL",
            quantity=10,
            average_buy_price=150.0,
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)

        assert holding.id is not None
        assert holding.user_id == user.id
        assert holding.ticker == "AAPL"
        assert holding.quantity == 10
        assert holding.average_buy_price == 150.0

    def test_updated_at_defaults_to_now(self, db):
        """updated_at is populated automatically when not supplied."""
        user = User(email="holder2@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        before = datetime.utcnow()
        holding = Holding(
            user_id=user.id,
            ticker="TSLA",
            quantity=5,
            average_buy_price=200.0,
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)
        after = datetime.utcnow()

        assert holding.updated_at is not None
        assert before <= holding.updated_at <= after

    def test_tablename(self):
        """The model maps to the 'holdings' table."""
        assert Holding.__tablename__ == "holdings"

    def test_relationship_to_user(self, db):
        """The 'user' relationship resolves back to the owning User."""
        user = User(email="holder3@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        holding = Holding(
            user_id=user.id,
            ticker="MSFT",
            quantity=3,
            average_buy_price=300.0,
        )
        db.add(holding)
        db.commit()
        db.refresh(holding)

        assert holding.user is not None
        assert holding.user.id == user.id
        assert holding.user.email == "holder3@test.com"

    def test_user_holdings_backref(self, db):
        """User.holdings exposes all holdings owned by that user."""
        user = User(email="holder4@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        holding1 = Holding(user_id=user.id, ticker="AAPL", quantity=1, average_buy_price=100.0)
        holding2 = Holding(user_id=user.id, ticker="GOOG", quantity=2, average_buy_price=1000.0)
        db.add_all([holding1, holding2])
        db.commit()
        db.refresh(user)

        tickers = {h.ticker for h in user.holdings}
        assert tickers == {"AAPL", "GOOG"}

    def test_multiple_holdings_per_ticker_allowed(self, db):
        """The model does not enforce uniqueness on (user_id, ticker)."""
        user = User(email="holder5@test.com", password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        holding1 = Holding(user_id=user.id, ticker="AAPL", quantity=1, average_buy_price=100.0)
        holding2 = Holding(user_id=user.id, ticker="AAPL", quantity=2, average_buy_price=110.0)
        db.add_all([holding1, holding2])
        db.commit()

        holdings = db.query(Holding).filter(Holding.user_id == user.id, Holding.ticker == "AAPL").all()
        assert len(holdings) == 2