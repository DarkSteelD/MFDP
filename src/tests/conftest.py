import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/ml_course"

from src.database.models import Base

pytest_plugins = ("pytest_asyncio",)

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ml_course_test"

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest_asyncio.fixture
async def db_connection(engine):
    async with engine.connect() as conn:
        await conn.execute(text("TRUNCATE users, transactions, predictions RESTART IDENTITY CASCADE"))
        await conn.commit()
        yield conn

@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_maker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()