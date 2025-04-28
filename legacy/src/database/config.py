import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres@localhost:5432/ml_course"
    )

DATABASE_URL = get_database_url()

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session 