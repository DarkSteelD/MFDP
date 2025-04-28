"""
Module: core.database

Provides database connectivity using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@database:5432/db")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db() -> None:
    """
    Initialize the database by creating all tables based on ORM models.

    Steps:
      - Import all ORM models to register them with the metadata.
      - Call Base.metadata.create_all(bind=engine).
    """
    # Import here to register models
    # from app.src.db.models import Base
    # Base.metadata.create_all(bind=engine)
    pass 