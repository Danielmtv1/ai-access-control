import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.config import get_settings
from app.shared.database.base import Base

# Get DB URL from settings and convert to asyncpg dialect
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get async DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close() 