"""
Module: dependencies

Defines common FastAPI dependencies used across routers.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from src.core.database import SessionLocal
from src.db.models import User
from src.core.config import SECRET_KEY, ALGORITHM
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
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid authentication token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(401, "User not found")
    return user


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
    if not current_user.is_active:
        raise HTTPException(403, "Inactive user")
    return current_user


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
    if not current_user.is_admin:
        raise HTTPException(403, "Unauthorized")
    return current_user
