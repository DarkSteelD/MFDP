"""
Module: routes.balance

Contains endpoints for balance operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.src.schemas.balance import BalanceRead, BalanceTopUp
from app.src.dependencies import get_db, get_current_active_user
from app.src.db.models import User


router = APIRouter(prefix="/balance", tags=["balance"])

@router.get("/", response_model=BalanceRead)
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's balance.

    Functional requirements:
      - Authenticate user via dependency.
      - Fetch user's balance from the database.
      - Return a BalanceRead model.
    """
    pass

@router.post("/topup", response_model=BalanceRead, status_code=status.HTTP_201_CREATED)
async def top_up_balance(
    request: BalanceTopUp,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Top up user's balance.

    Functional requirements:
      - Accept 'amount' and optional 'comment' in the request body.
      - Validate that amount > 0.
      - Create a deposit transaction in the database.
      - Update user's balance accordingly.
      - Return updated BalanceRead.
    """
    pass 