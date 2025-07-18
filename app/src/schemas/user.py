"""
Module: schemas.user

Contains Pydantic models for user operations.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    """
    Base schema with shared properties for users.

    Attributes:
      email: user's email address
    """
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """
    Schema for user registration.

    Attributes:
      password: raw password field, must meet complexity requirements
    """
    password: str = Field(..., min_length=8, description="User password of at least 8 characters")


class UserRead(UserBase):
    """
    Schema for reading user data from API.

    Attributes:
      id: user ID
      balance: current credit balance
      created_at: timestamp of registration
      is_admin: indicates administrative privileges
    """
    id: int = Field(..., description="Unique user identifier")
    balance: float = Field(..., ge=0, description="Current credit balance")
    created_at: datetime = Field(..., description="Timestamp of registration")
    is_admin: bool = Field(False, description="Administrative privileges flag")

    class Config:
        orm_mode = True
