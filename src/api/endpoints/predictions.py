import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from src.database.config import get_session
from src.database.models import User, MLModel, Prediction
from src.api.schemas import PredictionCreate, PredictionResponse, MLModelResponse
from src.api.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/models", response_model=List[MLModelResponse])
async def list_models(session: AsyncSession = Depends(get_session)):
    query = select(MLModel).filter(MLModel.is_active == True)
    result = await session.execute(query)
    models = result.scalars().all()
    return models


@router.get("/models/{model_id}", response_model=MLModelResponse)
async def get_model(model_id: int, session: AsyncSession = Depends(get_session)):
    query = select(MLModel).filter(MLModel.id == model_id)
    result = await session.execute(query)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
        
    if not model.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model is not active"
        )
        
    return model


@router.post("/predict", response_model=PredictionResponse)
async def make_prediction(
    prediction: PredictionCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(MLModel).filter(MLModel.id == prediction.model_id, MLModel.is_active == True)
    result = await session.execute(query)
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with ID {prediction.model_id} not found or is not active"
        )
    
    prediction_cost = 50
    if current_user.balance < prediction_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient balance. Required: {prediction_cost}, Available: {current_user.balance}"
        )
    start_time = time.time()
    
    output_data = {"result": "This is a simulated prediction result"}
    
    end_time = time.time()
    execution_time = (end_time - start_time) * 1000  
    db_prediction = Prediction(
        user_id=current_user.id,
        model_id=model.id,
        input_data=prediction.input_data,
        output_data=output_data,
        successful=True,
        created_at=datetime.now(),
        execution_time=execution_time
    )
    
    current_user.balance -= prediction_cost
    
    from src.database.models import Transaction
    transaction = Transaction(
        user_id=current_user.id,
        change=-prediction_cost,
        valid=True,
        time=datetime.now()
    )
    
    session.add(db_prediction)
    session.add(transaction)
    await session.commit()
    await session.refresh(db_prediction)
    
    return db_prediction


@router.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Prediction).filter(Prediction.user_id == current_user.id)
    result = await session.execute(query)
    predictions = result.scalars().all()
    
    return predictions


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id
    )
    result = await session.execute(query)
    prediction = result.scalar_one_or_none()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
        
    return prediction 