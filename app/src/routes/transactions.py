"""
Module: routes.transactions

Contains endpoints for transaction history.
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.transaction import TransactionRead
from src.dependencies import get_db, get_current_active_user
from src.db.models import Transaction, User as DBUser

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Alias without trailing slash to avoid 307 from /transactions -> /transactions/
@router.get("", response_model=List[TransactionRead])
async def get_transactions_alias(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )
    return transactions

@router.get("/", response_model=List[TransactionRead])
async def get_transactions(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    Get current user's transaction history.

    Steps:
      1. Authenticate user via dependency injection.
      2. Ensure user is active via dependency.
      3. Query the database for transactions belonging to the current user.
      4. Sort transactions by timestamp in descending order.
      5. Return a list of TransactionRead models.

    Args:
      db (Session): database session provided by dependency.
      current_user (User): authenticated and active user instance.

    Returns:
      List[TransactionRead]: list of user's transactions.

    Raises:
      HTTPException: 401 if user is not authenticated.
      HTTPException: 403 if user is inactive.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )
    return transactions
