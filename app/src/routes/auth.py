"""
Module: routes.auth

Contains endpoints for user registration and authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from src.core.security import verify_password, get_password_hash, create_access_token
from src.schemas.auth import Token
from src.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from src.dependencies import get_db
from src.db.models import User
from src.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> UserRead:
    """
    Register a new user.

    Steps:
      1. Check for existing user by email and reject duplicates.
      2. Hash the provided password securely.
      3. Create User ORM instance with zero balance and default is_admin flag.
      4. Persist user to the database and return serialized response.

    Returns:
      UserRead: details of the newly created user (without password hash).
    """
    # Check if email already registered
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create new user
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        balance=0.0,
        is_admin=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate user and issue JWT token.

    Steps:
      1. Retrieve user by email (username field of OAuth2 form).
      2. Verify provided password against stored hash.
      3. Create JWT access token embedding user ID in 'sub'.
      4. Return Token response with token and scheme.

    Returns:
      Token: access_token and token_type
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer") 