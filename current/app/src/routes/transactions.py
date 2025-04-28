"""
Module: routes.transactions

Contains endpoints for transaction history.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.src.schemas.transaction import TransactionRead
from app.src.dependencies import get_db, get_current_active_user
from app.src.db.models import User as DBUser

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/", response_model=List[TransactionRead])
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    Get current user's transaction history.

    Functional requirements:
      - Authenticate user via dependency.
      - Fetch all transactions for the current user from the database.
      - Return a list of TransactionRead models.
    """
    pass 