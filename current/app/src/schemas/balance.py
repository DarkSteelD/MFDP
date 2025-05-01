"""
Module: schemas.balance

Contains Pydantic models for balance operations.
"""

from pydantic import BaseModel, Field
from typing import Optional

class BalanceRead(BaseModel):
    """
    Schema for reading user's balance.

    Attributes:
      user_id: identifier of the user
      balance: current credit balance (non-negative float)
    """
    user_id : int = Field(..., description="Identifier of the user")
    balance : float = Field(..., ge=0, description="Current credit balance")

    class Config:
       orm_mode = True


class BalanceTopUp(BaseModel):
    """
    Schema for topping up user's balance.

    Attributes:
      amount: positive float amount to add to balance
      comment: optional description or note for this top-up
    """
    amount : float = Field(..., gt=0, description="Positive float amount to add to balance")
    comment : Optional[str] = Field(default=None, description="Optional description or note for this top-up")
