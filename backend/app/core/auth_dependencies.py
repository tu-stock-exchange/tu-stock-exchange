from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.dependencies import get_db
from app.models.users import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve and return the authenticated user from a JWT bearer token.

    Intended for use as a FastAPI dependency on any protected route.
    Extracts the token from the ``Authorization: Bearer <token>`` header,
    decodes it, and loads the corresponding user from the database.

    Args:
        token: JWT bearer token injected automatically by FastAPI from the
               ``Authorization`` header via ``OAuth2PasswordBearer``.
        db: Database session injected by FastAPI via ``get_db``.

    Returns:
        The ``User`` model instance for the authenticated user.

    Raises:
        HTTPException(401): If the token is missing, invalid, expired, or
            the user id embedded in the token no longer exists in the database.
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
