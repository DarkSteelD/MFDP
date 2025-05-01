"""
Module: routes.prediction

Contains endpoints for ML prediction operations.
"""

from typing import List, Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
import json
from aio_pika import connect_robust, Message

from src.schemas.prediction import PredictionRequest, PredictionResponse, DataValidationError
from src.dependencies import get_db, get_current_active_user
from src.db.models import User as DBUser, Transaction

router = APIRouter(prefix="/predict", tags=["prediction"])

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
IMAGE_QUEUE = os.getenv("IMAGE_QUEUE", "image_tasks")

@router.post("/", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    """
    Submit text or image data for ML predictions and charge user credits.

    Steps:
      1. Authenticate and ensure user is active via dependency injection.
      2. Validate that exactly one of 'text' or 'image' is provided (Pydantic schema enforces this).
      3. Verify current_user.balance is positive; raise HTTPException 400 if insufficient funds.
      4. Perform ML prediction on the provided input:
         - If 'text' provided, pass text to text-based model.
         - If 'image' provided, decode base64 and pass image to vision model.
      5. Calculate credits_spent based on the size of input or number of predictions.
      6. Deduct credits_spent from current_user.balance and create a 'prediction' transaction.
      7. Commit all database changes.
      8. Return a PredictionResponse with the appropriate prediction field and credits_spent.

    Args:
      request (PredictionRequest): contains either 'text' or 'image' field.
      db (Session): database session provided by dependency.
      current_user (User): authenticated and active user instance.

    Returns:
      PredictionResponse: contains 'text_prediction' or 'image_prediction' and credits_spent.

    Raises:
      HTTPException: 401 if user is not authenticated.
      HTTPException: 403 if user is inactive.
      HTTPException: 400 if user has insufficient balance.
    """
    # Ensure positive balance
    if current_user.balance <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    # Charge fixed credits for prediction
    credits_spent = 50.0
    # Create a 'prediction' transaction record
    transaction = Transaction(
        user_id=current_user.id,
        type="prediction",
        amount=credits_spent
    )
    db.add(transaction)
    # Deduct balance
    current_user.balance -= credits_spent
    db.add(current_user)
    db.commit()
    # Publish task to RabbitMQ
    body = json.dumps({
        "transaction_id": transaction.id,
        "image": request.image
    }).encode()
    connection = await connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.declare_queue(IMAGE_QUEUE, durable=True)
    await channel.default_exchange.publish(
        Message(body=body),
        routing_key=IMAGE_QUEUE
    )
    await connection.close()
    # Return response without immediate prediction
    return PredictionResponse(
        text_prediction=None,
        image_prediction=None,
        credits_spent=credits_spent
    )