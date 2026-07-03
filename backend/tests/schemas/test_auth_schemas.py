import pytest
from pydantic import ValidationError

from app.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)


class TestRegisterRequest:
    """Unit tests for the RegisterRequest schema."""

    def test_valid_payload(self):
        req = RegisterRequest(email="user@test.com", username="user1", password="secret123")
        assert req.email == "user@test.com"
        assert req.username == "user1"
        assert req.password == "secret123"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", username="user1", password="secret123")

    def test_missing_username_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@test.com", password="secret123")

    def test_missing_password_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@test.com", username="user1")

    def test_missing_email_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="user1", password="secret123")


class TestLoginRequest:
    """Unit tests for the LoginRequest schema."""

    def test_valid_payload(self):
        req = LoginRequest(email="user@test.com", password="secret123")
        assert req.email == "user@test.com"
        assert req.password == "secret123"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="secret123")

    def test_missing_password_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="user@test.com")


class TestUserResponse:
    """Unit tests for the UserResponse schema."""

    def test_valid_payload(self):
        resp = UserResponse(id=1, email="user@test.com", balance=10000.0, is_bankrupt=False)
        assert resp.id == 1
        assert resp.email == "user@test.com"
        assert resp.balance == 10000.0
        assert resp.is_bankrupt is False

    def test_missing_field_rejected(self):
        with pytest.raises(ValidationError):
            UserResponse(id=1, email="user@test.com", balance=10000.0)

    def test_from_attributes_supports_orm_objects(self):
        class FakeUser:
            id = 1
            email = "orm@test.com"
            balance = 500.0
            is_bankrupt = True

        resp = UserResponse.model_validate(FakeUser())
        assert resp.id == 1
        assert resp.email == "orm@test.com"
        assert resp.balance == 500.0
        assert resp.is_bankrupt is True


class TestTokenResponse:
    """Unit tests for the TokenResponse schema."""

    def test_default_token_type_is_bearer(self):
        resp = TokenResponse(access_token="abc123")
        assert resp.access_token == "abc123"
        assert resp.token_type == "bearer"

    def test_explicit_token_type_overrides_default(self):
        resp = TokenResponse(access_token="abc123", token_type="custom")
        assert resp.token_type == "custom"

    def test_missing_access_token_rejected(self):
        with pytest.raises(ValidationError):
            TokenResponse()