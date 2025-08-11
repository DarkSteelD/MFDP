"""
Module: schemas.transaction

Contains Pydantic models for transaction operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class TransactionBase(BaseModel):
    """
    Base schema for transaction data.

    Attributes:
      type: transaction type ('deposit' or 'prediction')
      amount: positive float credit amount
    """
    type: str = Field(..., description="Transaction type ('deposit' or 'prediction')")
    amount: float = Field(..., ge=0, description="Positive float credit amount")


class TransactionCreate(TransactionBase):
    """
    Schema for creating a new transaction.

    Attributes:
      Inherits all fields from TransactionBase.
    """
    pass


class TransactionRead(TransactionBase):
    """
    Schema for reading transaction data from API.

    Attributes:
      id: unique transaction identifier
      user_id: associated user identifier
      timestamp: datetime of transaction
    """
    id: int = Field(..., description="Unique transaction identifier")
    user_id: int = Field(..., description="Associated user identifier")
    timestamp: datetime = Field(..., description="Datetime of transaction")

    class Config:
        orm_mode = True
