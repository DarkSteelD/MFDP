import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database.models import User, Transaction, Prediction

@pytest.mark.asyncio
async def test_create_user(session):
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        is_admin=False,
        balance=100
    )
    session.add(user)
    await session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.balance == 100

@pytest.mark.asyncio
async def test_user_balance_update(session):
    user = User(
        username="testuser2",
        email="test2@example.com",
        password_hash="hashed_password",
        is_admin=False,
        balance=100
    )
    session.add(user)
    await session.commit()
    
    transaction = Transaction(
        user_id=user.id,
        change=50,
        valid=True,
        time=datetime.utcnow()
    )
    session.add(transaction)
    await session.commit()
    
    user.balance += transaction.change
    await session.commit()
    
    assert user.balance == 150

@pytest.mark.asyncio
async def test_create_prediction(session):
    user = User(
        username="testuser3",
        email="test3@example.com",
        password_hash="hashed_password",
        is_admin=False,
        balance=100
    )
    session.add(user)
    await session.commit()
    
    prediction = Prediction(
        user_id=user.id,
        input_data={"text": "test input"},
        output_data={"result": "test output"},
        successful=True,
        created_at=datetime.utcnow()
    )
    session.add(prediction)
    await session.commit()
    
    assert prediction.id is not None
    assert prediction.user_id == user.id

@pytest.mark.asyncio
async def test_user_relationships(session):
    user = User(
        username="testuser4",
        email="test4@example.com",
        password_hash="hashed_password",
        is_admin=False,
        balance=100
    )
    session.add(user)
    await session.commit()
    
    transaction = Transaction(
        user_id=user.id,
        change=25,
        valid=True,
        time=datetime.utcnow()
    )
    session.add(transaction)
    await session.commit()
    
    prediction = Prediction(
        user_id=user.id,
        input_data={"text": "test input"},
        output_data={"result": "test output"},
        successful=True,
        created_at=datetime.utcnow()
    )
    session.add(prediction)
    await session.commit()
    
    stmt = select(User).options(
        selectinload(User.transactions),
        selectinload(User.predictions)
    ).filter(User.id == user.id)
    
    result = await session.execute(stmt)
    user_with_relations = result.scalars().first()
    
    assert len(user_with_relations.transactions) == 1
    assert len(user_with_relations.predictions) == 1 