from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    A unique salt is generated automatically on each call, so the same
    password will produce a different hash every time.

    Args:
        password: The plain-text password to hash.

    Returns:
        A bcrypt hash string safe to store in the database.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a plain-text password matches a stored bcrypt hash.

    Args:
        plain_password: The password submitted by the user.
        hashed_password: The bcrypt hash retrieved from the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create a signed JWT access token containing the given payload.

    The token is signed with HS256 using SECRET_KEY and expires after
    ACCESS_TOKEN_EXPIRE_MINUTES (default 60 minutes).

    Args:
        data: Arbitrary claims to embed in the token payload.
              Must include ``"sub"`` (subject, typically the user id as a string).

    Returns:
        A signed JWT string to be sent to the client as a bearer token.
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT access token.

    Verifies the token signature against SECRET_KEY and checks that it has
    not expired. Returns None for any failure — invalid signature, wrong
    algorithm, malformed token, or expiry — so callers never need to catch
    exceptions from this function.

    Args:
        token: The raw JWT string received from the client.

    Returns:
        The decoded payload dict if the token is valid and unexpired,
        or None if validation fails for any reason.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
