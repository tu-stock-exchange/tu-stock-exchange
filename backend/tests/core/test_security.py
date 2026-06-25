import time
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)



# Password hashing


class TestHashPassword:

    def test_returns_string(self):
        result = hash_password("secret")
        assert isinstance(result, str)

    def test_hash_is_not_plain_text(self):
        result = hash_password("secret")
        assert result != "secret"

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt each call
        h1 = hash_password("secret")
        h2 = hash_password("secret")
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self):
        result = hash_password("secret")
        assert result.startswith("$2b$") or result.startswith("$2a$")



# Password verification


class TestVerifyPassword:

    def test_correct_password_returns_true(self):
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_password_does_not_match_non_empty_hash(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        hashed = hash_password("Secret")
        assert verify_password("secret", hashed) is False

    def test_round_trip(self):
        password = "MyP@ssw0rd!"
        assert verify_password(password, hash_password(password)) is True



# JWT creation


class TestCreateAccessToken:

    def test_returns_string(self):
        token = create_access_token({"sub": "1"})
        assert isinstance(token, str)

    def test_token_has_three_parts(self):
        token = create_access_token({"sub": "1"})
        assert len(token.split(".")) == 3

    def test_different_data_produces_different_tokens(self):
        t1 = create_access_token({"sub": "1"})
        t2 = create_access_token({"sub": "2"})
        assert t1 != t2


# JWT decoding

class TestDecodeAccessToken:

    def test_valid_token_returns_payload(self):
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"

    def test_exp_claim_is_present(self):
        token = create_access_token({"sub": "1"})
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_invalid_token_returns_none(self):
        result = decode_access_token("not.a.token")
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "1"})
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_expired_token_returns_none(self):
        with patch("app.core.security.settings") as mock_settings:
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 0
            mock_settings.SECRET_KEY = "testsecret"
            mock_settings.ALGORITHM = "HS256"
            token = create_access_token({"sub": "1"})

        time.sleep(1)
        result = decode_access_token(token)
        assert result is None

    def test_empty_string_returns_none(self):
        assert decode_access_token("") is None
