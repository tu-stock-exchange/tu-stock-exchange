from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.auth_schemas import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.db.dependencies import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account.

    Creates a user with the given email, username, and a bcrypt-hashed
    password. The email is lowercased before storage so that lookups are
    case-insensitive. New accounts start with a balance of $10,000 and
    are not bankrupt.

    Args:
        data: Registration payload containing ``email``, ``username``,
              and ``password``.
        db: Database session injected by FastAPI.

    Returns:
        The newly created user's public profile (id, email, balance,
        is_bankrupt). The password hash is never included in the response.

    Raises:
        HTTPException(400): If the email address is already registered.
    """
    email = data.email.lower()

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=email,
        username=data.username,
        password_hash=hash_password(data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token.

    Looks up the user by email (case-insensitive), verifies the password
    against the stored bcrypt hash, and issues a signed JWT bearer token
    on success. The token contains the user id as the ``sub`` claim and
    expires after ``ACCESS_TOKEN_EXPIRE_MINUTES`` (default 60 minutes).

    Args:
        data: Login payload containing ``email`` and ``password``.
        db: Database session injected by FastAPI.

    Returns:
        A ``TokenResponse`` with ``access_token`` (JWT string) and
        ``token_type`` (always ``"bearer"``).

    Raises:
        HTTPException(401): If the email is not found or the password does
            not match. The error message is intentionally vague to prevent
            user enumeration.
    """
    email = data.email.lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
