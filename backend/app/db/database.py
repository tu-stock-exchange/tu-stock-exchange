from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = settings.DATABASE_URL #it is loaded from the .env file using the Pydantic Settings class defined in app.core.config.py

# Convert asyncpg URL to sync psycopg2 URL (for Alembic)
def get_sync_url() -> str:
    """Convert async postgresql+asyncpg:// to sync postgresql://"""
    return settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://"
    ).replace(
        "postgresql+asyncpg://", "postgresql://"
    )  # Second replace for safety

# ⚡ Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# 🔁 Sync engine for Alembic (created only when needed)
def get_sync_engine():
    return create_engine(get_sync_url())

Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

sync_engine = get_sync_engine()
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)