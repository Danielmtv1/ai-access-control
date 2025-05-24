import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
from typing import AsyncGenerator
from ..config import get_settings

# Get DB URL from settings and convert to asyncpg dialect
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(ASYNC_DATABASE_URL)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get async DB session
async def get_db() -> AsyncGenerator[Session, None]:
    async with AsyncSessionLocal() as db:
        yield db

