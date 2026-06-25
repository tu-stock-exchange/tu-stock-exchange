# Authentication Feature

## 1. Purpose

Authentication controls who can access the platform and proves identity on every protected request. The system uses **email + password** registration with **JWT (JSON Web Token)** bearer tokens for stateless session management. Passwords are never stored in plain text — only bcrypt hashes are persisted.

Every route that requires a logged-in user (trading, portfolio, auto-trades, etc.) validates the token on each request via the `get_current_user` dependency.

---

## 2. Related Endpoints

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| `POST` | `/api/auth/register` | No | Create a new account |
| `POST` | `/api/auth/login` | No | Exchange credentials for a JWT token |
| `GET`  | `/api/users/me` | Yes | Get the current user's profile |
| `PUT`  | `/api/users/me` | Yes | Update the current user's email |

All other `/api/*` routes also require a valid token.

---

## 3. Request and Response Examples

### Register

**Request**
```
POST /api/auth/register
Content-Type: application/json

{
  "email": "alice@example.com",
  "username": "alice",
  "password": "mypassword123"
}
```

**Response `201 Created`**
```json
{
  "id": 1,
  "email": "alice@example.com",
  "balance": 10000.0,
  "is_bankrupt": false
}
```

---

### Login

**Request**
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "mypassword123"
}
```

**Response `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Using the token on a protected route

Include the token in the `Authorization` header on every request to a protected endpoint:

```
GET /api/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response `200 OK`**
```json
{
  "id": 1,
  "email": "alice@example.com",
  "balance": 10000.0,
  "is_bankrupt": false,
  "bankrupt_at": null,
  "registered_at": "2026-06-25T10:00:00"
}
```

---

## 4. Important Business Rules

- **Email is case-insensitive**: emails are lowercased before storing and before lookup, so `Alice@Example.com` and `alice@example.com` refer to the same account.
- **Unique email**: registering with an already-used email returns `400`.
- **Password hashing**: passwords are hashed with **bcrypt** via `passlib`. The plain-text password is never stored or logged.
- **Token algorithm**: `HS256` (HMAC-SHA256), signed with `SECRET_KEY` from environment config.
- **Token expiry**: tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default **60 minutes**). After expiry the user must log in again.
- **Token payload**: contains only `{ "sub": "<user_id>", "exp": <unix_timestamp> }`. No roles or permissions are embedded.
- **Stateless**: the server keeps no session state. Every request is authenticated independently by decoding the JWT.

---

## 5. Error Cases

| Situation | Status | Detail message |
|-----------|--------|----------------|
| Email already registered | `400` | `"Email already registered"` |
| Wrong email or password on login | `401` | `"Invalid email or password"` |
| Missing `Authorization` header | `401` | `"Not authenticated"` |
| Token signature invalid or tampered | `401` | `"Invalid or expired token"` |
| Token expired | `401` | `"Invalid or expired token"` |
| Token valid but user deleted from DB | `401` | `"User not found"` |

---

## 6. Related Database Models

### `users` table

| Column | Used by auth | Description |
|--------|-------------|-------------|
| `id` | Yes | Stored as `sub` claim in the JWT |
| `email` | Yes | Unique login identifier, lowercased |
| `username` | No | Display name, not used for login |
| `password_hash` | Yes | bcrypt hash checked during login |
| `registered_at` | No | Set automatically on registration |

> See `docs/db_schema.md` for full schema details.

### Key source files

| File | Role |
|------|------|
| `app/routers/auth.py` | Register and login endpoints |
| `app/core/security.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_access_token` |
| `app/core/auth_dependencies.py` | `get_current_user` FastAPI dependency — validates token on every protected request |
| `app/core/config.py` | `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` from environment |
| `app/schemas/auth_schemas.py` | Pydantic schemas: `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse` |

---

## 7. How to Test the Feature

### Automated tests

Auth tests live in:

```
backend/tests/test_auth.py
```

Run with:

```bash
pytest backend/tests/test_auth.py -v
```

### Manual testing flow

**Register a new user**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "secret123"}'
```

**Log in and save the token**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secret123"}'
```

Copy the `access_token` from the response.

**Access a protected route**
```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <your_token_here>"
```

**Verify token rejection**
```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer invalid.token.here"
# expect 401 Invalid or expired token
```

**Verify duplicate registration is blocked**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "other", "password": "abc"}'
# expect 400 Email already registered
```

### Configuration

The following environment variables control auth behaviour (set in `.env` or Docker environment):

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | Required. Random secret used to sign JWTs. Must be kept private. |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime in minutes |
