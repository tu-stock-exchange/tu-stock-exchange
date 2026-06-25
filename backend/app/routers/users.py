from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.users import User
from app.schemas.users_schemas import UserPublicResponse, UserUpdateRequest
from app.services.default_services import recover_from_bankruptcy


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublicResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

@router.post("/me/recover", response_model=UserPublicResponse)
def recover_bankruptcy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_bankrupt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not bankrupt",
        )
    return recover_from_bankruptcy(current_user, db)


@router.put("/me", response_model=UserPublicResponse)
def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.email:
        current_user.email = data.email

    db.commit()
    db.refresh(current_user)

    return current_user