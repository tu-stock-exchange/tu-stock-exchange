from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.users_schemas import UserPublicResponse, UserUpdateRequest


class TestUserPublicResponse:
    """Unit tests for the UserPublicResponse schema."""

    def test_valid_payload(self):
        now = datetime.utcnow()
        resp = UserPublicResponse(
            id=1,
            email="user@test.com",
            balance=10000.0,
            is_bankrupt=False,
            bankrupt_at=None,
            registered_at=now,
        )
        assert resp.id == 1
        assert resp.email == "user@test.com"
        assert resp.balance == 10000.0
        assert resp.is_bankrupt is False
        assert resp.bankrupt_at is None
        assert resp.registered_at == now

    def test_bankrupt_at_can_be_a_datetime(self):
        now = datetime.utcnow()
        resp = UserPublicResponse(
            id=2,
            email="bankrupt@test.com",
            balance=0.0,
            is_bankrupt=True,
            bankrupt_at=now,
            registered_at=now,
        )
        assert resp.bankrupt_at == now

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            UserPublicResponse(
                id=1,
                email="user@test.com",
                balance=10000.0,
                is_bankrupt=False,
                bankrupt_at=None,
                # registered_at missing
            )

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserPublicResponse(
                id=1,
                email="not-an-email",
                balance=10000.0,
                is_bankrupt=False,
                bankrupt_at=None,
                registered_at=datetime.utcnow(),
            )

    def test_from_attributes_supports_orm_objects(self):
        class FakeUser:
            id = 1
            email = "orm@test.com"
            balance = 1234.5
            is_bankrupt = False
            bankrupt_at = None
            registered_at = datetime(2024, 1, 1)

        resp = UserPublicResponse.model_validate(FakeUser())
        assert resp.id == 1
        assert resp.email == "orm@test.com"
        assert resp.registered_at == datetime(2024, 1, 1)


class TestUserUpdateRequest:
    """Unit tests for the UserUpdateRequest schema."""

    def test_valid_email_update(self):
        req = UserUpdateRequest(email="updated@test.com")
        assert req.email == "updated@test.com"

    def test_email_defaults_to_none(self):
        req = UserUpdateRequest()
        assert req.email is None

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest(email="not-an-email")

    def test_explicit_none_is_accepted(self):
        req = UserUpdateRequest(email=None)
        assert req.email is None