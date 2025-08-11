"""
Module: core.security

Contains utilities for password hashing and JWT token operations.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt

from src.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Initialize Passlib context for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against the stored hash.

    Args:
      plain_password: raw password provided by the user
      hashed_password: bcrypt hash stored in the database

    Returns:
      True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password for secure storage.

    Args:
      password: raw password

    Returns:
      A bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT token with the given payload and expiration time.

    Args:
      data: payload data to encode (e.g., {"sub": "user_id"})
      expires_delta: optional timedelta for token expiration

    Returns:
      Encoded JWT token as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt 