from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserPublicResponse(BaseModel):
    id: int
    email: EmailStr
    balance: float
    is_bankrupt: bool
    bankrupt_at: Optional[datetime]
    registered_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
