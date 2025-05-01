from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Dict, Any, Optional, List


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(UserBase):
    id: int
    balance: int
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class PredictionCreate(BaseModel):
    model_id: int
    input_data: Dict[str, Any]


class PredictionResponse(BaseModel):
    id: int
    user_id: int
    model_id: int
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    successful: bool
    created_at: datetime
    execution_time: Optional[float] = None

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    amount: int = Field(..., gt=0, description="Amount to add to the balance")


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    change: int
    valid: bool
    time: datetime

    class Config:
        from_attributes = True


class MLModelResponse(BaseModel):
    id: int
    name: str
    description: str
    version: str
    creation_date: datetime
    is_active: bool
    model_type: str
    parameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class UserBalance(BaseModel):
    balance: int 