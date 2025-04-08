import pytest
from src.database.models import User, Transaction, Prediction, MLModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@pytest.mark.asyncio
async def test_basic_models(db_session):
    """Test basic model creation and relationships."""
    # Create a user
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password",
        is_admin=False,
        balance=100
    )
    db_session.add(user)
    await db_session.commit()
    
    assert user.id is not None
    assert user.username == "test_user"
    assert user.balance == 100
    
    model = MLModel(
        name="Test Model",
        description="A test model",
        version="1.0",
        model_type="test",
        is_active=True,
        parameters={"param1": "value1"},
        metrics={"accuracy": 0.95}
    )
    db_session.add(model)
    await db_session.commit()
    
    transaction = Transaction(
        user_id=user.id,
        change=50,
        valid=True
    )
    db_session.add(transaction)
    await db_session.commit()
    
    user.balance += transaction.change
    await db_session.commit()
    
    assert user.balance == 150
    
    prediction = Prediction(
        user_id=user.id,
        model_id=model.id,
        input_data={"input": "test data"},
        output_data={"result": "test result"},
        successful=True
    )
    db_session.add(prediction)
    await db_session.commit()
    
    assert prediction.id is not None
    assert prediction.user_id == user.id
    assert prediction.model_id == model.id

@pytest.mark.asyncio
async def test_relationship_loading(db_session):
    """Test loading of relationships between models."""
    user = User(username="relation_user", email="relation@example.com", balance=200)
    db_session.add(user)
    await db_session.commit()
    
    model1 = MLModel(name="Model 1", version="1.0", model_type="regression")
    model2 = MLModel(name="Model 2", version="2.0", model_type="classification")
    db_session.add_all([model1, model2])
    await db_session.commit()
    
    transactions = [
        Transaction(user_id=user.id, change=100, valid=True),
        Transaction(user_id=user.id, change=-50, valid=True)
    ]
    db_session.add_all(transactions)
    await db_session.commit()
    
    predictions = [
        Prediction(
            user_id=user.id, 
            model_id=model1.id,
            input_data={"data": 1},
            output_data={"result": 10},
            successful=True
        ),
        Prediction(
            user_id=user.id, 
            model_id=model2.id,
            input_data={"image": "test.jpg"},
            output_data={"class": "cat"},
            successful=True
        )
    ]
    db_session.add_all(predictions)
    await db_session.commit()
    
    stmt = select(User).options(
        selectinload(User.transactions),
        selectinload(User.predictions)
    ).filter(User.id == user.id)
    
    result = await db_session.execute(stmt)
    user_with_relations = result.scalars().first()
    
    assert len(user_with_relations.transactions) == 2
    assert len(user_with_relations.predictions) == 2
    
    stmt = select(MLModel).options(
        selectinload(MLModel.predictions)
    ).filter(MLModel.id == model1.id)
    
    result = await db_session.execute(stmt)
    model_with_relations = result.scalars().first()
    
    assert len(model_with_relations.predictions) == 1
    assert model_with_relations.predictions[0].input_data == {"data": 1}

@pytest.mark.asyncio
async def test_negative_scenarios(db_session):
    user = User(username="unique_user", email="unique@example.com")
    db_session.add(user)
    await db_session.commit()
    
    duplicate_user = User(username="unique_user", email="different@example.com")
    db_session.add(duplicate_user)
    
    try:
        await db_session.commit()
        assert False, "Expected an exception for duplicate username"
    except Exception as e:
        await db_session.rollback()
        assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
    
    invalid_prediction = Prediction(
        user_id=999, 
        model_id=999, 
        input_data={"test": "data"},
        output_data={"result": "test"},
        successful=True
    )
    db_session.add(invalid_prediction)
    
    try:
        await db_session.commit()
        assert False, "Expected an exception for invalid foreign keys"
    except Exception as e:
        await db_session.rollback()
        assert "foreign key" in str(e).lower() or "violates" in str(e).lower() 