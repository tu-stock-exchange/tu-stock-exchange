from app.core.security import create_access_token



# POST /auth/register


class TestRegister:

    def test_success_returns_201(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "alice@example.com", "username": "alice", "password": "pass123"},
        )
        assert response.status_code == 201

    def test_response_contains_expected_fields(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "bob@example.com", "username": "bob", "password": "pass123"},
        )
        data = response.json()
        assert "id" in data
        assert data["email"] == "bob@example.com"
        assert data["balance"] == 10000.0
        assert data["is_bankrupt"] is False

    def test_password_not_exposed_in_response(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "safe@example.com", "username": "safe", "password": "secret"},
        )
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_duplicate_email_returns_400(self, client):
        payload = {"email": "dup@example.com", "username": "dup", "password": "pass123"}
        client.post("/api/auth/register", json=payload)
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    def test_email_stored_lowercase(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "UPPER@Example.COM", "username": "upper", "password": "pass123"},
        )
        assert response.json()["email"] == "upper@example.com"

    def test_duplicate_email_case_insensitive(self, client):
        client.post(
            "/api/auth/register",
            json={"email": "case@example.com", "username": "case1", "password": "pass"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "CASE@EXAMPLE.COM", "username": "case2", "password": "pass"},
        )
        assert response.status_code == 400

    def test_missing_email_returns_422(self, client):
        response = client.post(
            "/api/auth/register",
            json={"username": "nomail", "password": "pass123"},
        )
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "nopass@example.com", "username": "nopass"},
        )
        assert response.status_code == 422

    def test_invalid_email_format_returns_422(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "username": "bad", "password": "pass123"},
        )
        assert response.status_code == 422



# POST /auth/login


class TestLogin:

    def _register(self, client, email="user@example.com", username="user", password="pass123"):
        client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": password},
        )

    def test_success_returns_token(self, client):
        self._register(client)
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "pass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_token_is_non_empty_string(self, client):
        self._register(client, "tok@example.com", "tok")
        response = client.post(
            "/api/auth/login",
            json={"email": "tok@example.com", "password": "pass123"},
        )
        token = response.json()["access_token"]
        assert isinstance(token, str) and len(token) > 0

    def test_wrong_password_returns_401(self, client):
        self._register(client, "wp@example.com", "wp")
        response = client.post(
            "/api/auth/login",
            json={"email": "wp@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_unknown_email_returns_401(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "pass123"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_email_case_insensitive(self, client):
        self._register(client, "mixed@example.com", "mixed")
        response = client.post(
            "/api/auth/login",
            json={"email": "MIXED@EXAMPLE.COM", "password": "pass123"},
        )
        assert response.status_code == 200

    def test_missing_password_returns_422(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422



# Protected routes — token validation via GET /api/users/me


class TestTokenProtection:

    def _get_token(self, client, email="auth@example.com", username="authuser"):
        client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": "pass123"},
        )
        resp = client.post(
            "/api/auth/login",
            json={"email": email, "password": "pass123"},
        )
        return resp.json()["access_token"]

    def test_valid_token_grants_access(self, client):
        token = self._get_token(client)
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == "auth@example.com"

    def test_no_token_returns_401(self, client):
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_tampered_token_returns_401(self, client):
        token = self._get_token(client, "tamper@example.com", "tamper")
        bad_token = token[:-5] + "XXXXX"
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert response.status_code == 401

    def test_token_for_deleted_user_returns_401(self, client, db):
        from app.models.users import User

        token = self._get_token(client, "gone@example.com", "gone")

        user = db.query(User).filter(User.email == "gone@example.com").first()
        db.delete(user)
        db.commit()

        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        # Manually create a token that is already expired (exp in the past)
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.core.config import settings

        payload = {
            "sub": "9999",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
