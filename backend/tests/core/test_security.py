from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_different_value():
    plain_password = "password123"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0


def test_verify_password_with_correct_password_returns_true():
    plain_password = "password123"
    hashed_password = hash_password(plain_password)

    result = verify_password(plain_password, hashed_password)

    assert result is True


def test_verify_password_with_wrong_password_returns_false():
    plain_password = "password123"
    hashed_password = hash_password(plain_password)

    result = verify_password("wrong-password", hashed_password)

    assert result is False


def test_create_access_token_contains_payload_data():
    token = create_access_token({"sub": "test@example.com"})

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


def test_decode_access_token_with_valid_token_returns_payload():
    token = create_access_token({"sub": "test@example.com"})

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


def test_decode_access_token_with_invalid_token_returns_none():
    payload = decode_access_token("invalid.token.value")

    assert payload is None