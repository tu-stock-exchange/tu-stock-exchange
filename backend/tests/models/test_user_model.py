from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.users import User


class TestUserModel:
    """Unit tests for the User SQLAlchemy model."""

    def test_create_user_with_defaults(self, db):
        """Creating a user without balance/is_bankrupt applies model defaults."""
        user = User(email="new@test.com", password_hash="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None
        assert user.email == "new@test.com"
        assert user.password_hash == "hashed"
        assert user.balance == 10000
        assert user.is_bankrupt is False
        assert user.bankrupt_at is None
        assert user.registered_at is not None

    def test_create_user_with_explicit_values(self, db):
        """Explicit fields override model defaults."""
        user = User(
            email="rich@test.com",
            username="richie",
            password_hash="hashed",
            balance=99999.0,
            is_bankrupt=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.username == "richie"
        assert user.balance == 99999.0
        assert user.is_bankrupt is True

    def test_registered_at_defaults_to_now(self, db):
        """registered_at is populated automatically when not supplied."""
        before = datetime.utcnow()
        user = User(email="timed@test.com", password_hash="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)
        after = datetime.utcnow()

        assert before <= user.registered_at <= after

    def test_email_uniqueness_enforced(self, db):
        """Two users cannot share the same email address."""
        user1 = User(email="dup@test.com", password_hash="a")
        db.add(user1)
        db.commit()

        user2 = User(email="dup@test.com", password_hash="b")
        db.add(user2)

        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_username_uniqueness_enforced(self, db):
        """Two users cannot share the same username."""
        user1 = User(email="a1@test.com", username="sameuser", password_hash="a")
        db.add(user1)
        db.commit()

        user2 = User(email="a2@test.com", username="sameuser", password_hash="b")
        db.add(user2)

        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_username_is_optional(self, db):
        """A user can be created without a username."""
        user = User(email="nouser@test.com", password_hash="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.username is None

    def test_bankrupt_at_nullable(self, db):
        """bankrupt_at stays None until explicitly set."""
        user = User(email="notbankrupt@test.com", password_hash="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.bankrupt_at is None

    def test_bankrupt_at_can_be_set(self, db):
        """bankrupt_at records the timestamp of a bankruptcy event."""
        bankruptcy_time = datetime(2024, 6, 1, 12, 0, 0)
        user = User(
            email="bankrupt@test.com",
            password_hash="hashed",
            is_bankrupt=True,
            bankrupt_at=bankruptcy_time,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.is_bankrupt is True
        assert user.bankrupt_at == bankruptcy_time

    def test_tablename(self):
        """The model maps to the 'users' table."""
        assert User.__tablename__ == "users"

    def test_holdings_relationship_empty_by_default(self, db):
        """A newly created user starts with no holdings."""
        user = User(email="noholdings@test.com", password_hash="hashed")
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.holdings == []