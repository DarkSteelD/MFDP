# import os # Keep commented if unused
import os
# import asyncio # Keep commented if unused
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.database.models import Base

pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    config.option.asyncio_mode = "auto"

# Use SQLite for testing as it's lightweight and doesn't require a separate server
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/ml_course_test"
)

@pytest_asyncio.fixture(scope="function")
async def test_db_session():
    """Provides a clean database session for each test function."""
    engine = create_async_engine(DATABASE_URL, future=True)
    
    async with engine.begin() as conn:
        # Drop all tables in the test database
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables in the test database
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a new session with our test engine
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    session = async_session()
    
    try:
        yield session
    finally:
        # Clean up resources
        await session.close()
        await engine.dispose()