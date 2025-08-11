"""
Module: routes.balance

Contains endpoints for balance operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.schemas.balance import BalanceRead, BalanceTopUp
from src.dependencies import get_db, get_current_active_user
from src.db.models import Transaction, User


router = APIRouter(prefix="/balance", tags=["balance"])

# Alias without trailing slash to avoid 307 from /balance -> /balance/
@router.get("", response_model=BalanceRead)
async def get_balance_alias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return BalanceRead(user_id=current_user.id, balance=current_user.balance)

@router.get("/", response_model=BalanceRead)
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's balance.

    Steps:
      1. Authenticate and ensure user is active via dependency injection.
      2. Retrieve balance directly from current_user model (float).
      3. Return a BalanceRead instance.

    Args:
      db (Session): database session provided by dependency.
      current_user (User): authenticated and active user instance.

    Returns:
      BalanceRead: contains user_id and current credit balance.

    Raises:
      HTTPException: 401 if user is not authenticated.
      HTTPException: 403 if user is inactive.
    """
    return BalanceRead(user_id=current_user.id, balance=current_user.balance)

@router.post("/topup", response_model=BalanceRead, status_code=status.HTTP_201_CREATED)
async def top_up_balance(
    request: BalanceTopUp,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Top up user's balance by creating a deposit transaction.

    Steps:
      1. Validate that request.amount > 0 via Pydantic schema.
      2. Create a Transaction of type 'deposit' linked to current_user.
      3. Update current_user.balance by adding request.amount.
      4. Commit the transaction and updated balance to the database.
      5. Refresh user model and return updated balance.

    Args:
      request (BalanceTopUp): contains amount and optional comment.
      db (Session): database session provided by dependency.
      current_user (User): authenticated and active user instance.

    Returns:
      BalanceRead: contains user_id and updated credit balance.

    Raises:
      HTTPException: 400 if amount invalid.
      HTTPException: 401 if user is not authenticated.
    """
    # Create the deposit transaction
    transaction = Transaction(
        user_id=current_user.id,
        type="deposit",
        amount=request.amount,
        comment=request.comment
    )
    db.add(transaction)
    # Update user's balance
    current_user.balance += request.amount
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    # Ensure refreshed relationship state
    db.expunge_all()
    refreshed_user = db.query(User).get(current_user.id)
    return BalanceRead(user_id=refreshed_user.id, balance=refreshed_user.balance)