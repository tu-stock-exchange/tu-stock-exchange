from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    """Database model representing a registered platform user.

    Stores account credentials, current cash balance, and bankruptcy state.
    The password is never stored in plain text — only a bcrypt hash is kept.

    Attributes:
        id: Auto-incremented primary key.
        email: Unique email address, always stored in lowercase.
        username: Optional unique display name.
        password_hash: bcrypt hash of the user's password.
        balance: Current cash balance in USD. Starts at $10,000 for new users.
        is_bankrupt: True when the account is locked due to bankruptcy.
            Trading is blocked while this flag is set.
        bankrupt_at: UTC timestamp of the most recent bankruptcy event.
            Set automatically when bankruptcy is declared; not cleared on
            recovery — acts as a permanent historical record.
        registered_at: UTC timestamp when the account was created.
        holdings: Relationship to the user's current portfolio holdings.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String)
    balance = Column(Float, default=10000)
    is_bankrupt = Column(Boolean, default=False)
    bankrupt_at = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    holdings = relationship("Holding", back_populates="user")
