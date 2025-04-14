from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.database.config import get_session
from src.database.models import User, Transaction
from src.api.schemas import UserBalance, TransactionCreate, TransactionResponse
from src.api.auth import get_current_active_user

router = APIRouter()


@router.get("/balance", response_model=UserBalance)
async def get_balance(current_user: User = Depends(get_current_active_user)):
    return {"balance": current_user.balance}


@router.post("/balance/add", response_model=TransactionResponse)
async def add_balance(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    db_transaction = Transaction(
        user_id=current_user.id,
        change=transaction.amount,
        valid=True,
        time=datetime.now()
    )
    
    session.add(db_transaction)
    
    current_user.balance += transaction.amount
    
    await session.commit()
    await session.refresh(db_transaction)
    
    return db_transaction


@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Transaction).filter(Transaction.user_id == current_user.id)
    result = await session.execute(query)
    transactions = result.scalars().all()
    
    return transactions 