"""
Module: dependencies

Defines common FastAPI dependencies used across routers.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.src.core.database import SessionLocal
from app.src.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session to path operations and ensure it's closed after.

    Yields:
      Session: SQLAlchemy session tied to the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Decode and verify JWT token, then fetch the corresponding user from the database.

    Steps:
      - Decode the JWT and verify signature and expiration.
      - Extract user ID or email from payload.
      - Query the database for the User record.
      - If token invalid or user not found, raise HTTPException 401.

    Returns:
      User: authenticated user instance.
    """
    pass


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user is active (not banned or deactivated).

    Raises:
      HTTPException 403 if user is inactive.

    Returns:
      User: active user instance.
    """
    pass


async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure the current user has administrative privileges.

    Raises:
      HTTPException 403 if user is not an admin.

    Returns:
      User: admin user instance.
    """
    pass 