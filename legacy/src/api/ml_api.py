import os
import base64
import io
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api.ml_task_producer import MLTaskProducer
from src.database.config import get_session
from src.database.models import User, Transaction
from src.api.auth import get_current_active_user, get_current_admin_user

app = FastAPI(
    title="ML Service API",
    description="API for interacting with ML models via a message queue",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "ml_tasks")

MODEL_COSTS = {
    "text_generation": 10,
    "spam_detection": 5,
    "image_caption": 15
}

class TextGenerationRequest(BaseModel):
    text: str
    max_length: Optional[int] = 100
    temperature: Optional[float] = 0.7

class SpamDetectionRequest(BaseModel):
    text: str
    detailed: Optional[bool] = False

class TaskResponse(BaseModel):
    task_id: str
    status: str = "processing"
    error: Optional[str] = None

class TextGenerationResponse(TaskResponse):
    generated_text: Optional[str] = None
    execution_time: Optional[float] = None
    prediction_id: Optional[int] = None

class SpamDetectionResponse(TaskResponse):
    classification: Optional[str] = None
    scores: Optional[Dict[str, float]] = None
    execution_time: Optional[float] = None
    prediction_id: Optional[int] = None

class ImageCaptionResponse(TaskResponse):
    caption: Optional[str] = None
    execution_time: Optional[float] = None
    prediction_id: Optional[int] = None

class PaymentRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount to add to the balance")
    payment_method: str = "card"
    payment_details: Dict[str, Any] = {}

class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    amount: int
    redirect_url: Optional[str] = None

def get_task_producer():
    producer = MLTaskProducer(RABBITMQ_URL, QUEUE_NAME)
    try:
        yield producer
    finally:
        producer.close()

async def check_user_balance(user: User, task_type: str, session: AsyncSession) -> bool:
    cost = MODEL_COSTS.get(task_type, 10)
    
    if user.balance < cost:
        return False
    
    return True

@app.get("/")
async def root():
    return {"status": "ok", "message": "ML Service API is running"}

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    request: TextGenerationRequest,
    background_tasks: BackgroundTasks,
    wait: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    producer: MLTaskProducer = Depends(get_task_producer)
):
    if not await check_user_balance(current_user, "text_generation", session):
        raise HTTPException(
            status_code=402,
            detail="Insufficient balance to perform this operation. Please add credits to your account."
        )
    
    response = producer.send_text_generation_task(
        text=request.text,
        user_id=current_user.id,
        max_length=request.max_length,
        temperature=request.temperature,
        wait_for_response=wait
    )
    
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    if not wait:
        return TaskResponse(task_id=response["task_id"], status="processing")
    
    return TextGenerationResponse(
        task_id=response["task_id"],
        status="completed",
        generated_text=response.get("generated_text", None),
        execution_time=response.get("execution_time", None),
        prediction_id=response.get("prediction_id", None)
    )

@app.post("/detect-spam", response_model=SpamDetectionResponse)
async def detect_spam(
    request: SpamDetectionRequest,
    background_tasks: BackgroundTasks,
    wait: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    producer: MLTaskProducer = Depends(get_task_producer)
):
    if not await check_user_balance(current_user, "spam_detection", session):
        raise HTTPException(
            status_code=402,
            detail="Insufficient balance to perform this operation. Please add credits to your account."
        )
    
    response = producer.send_spam_detection_task(
        text=request.text,
        user_id=current_user.id,
        detailed=request.detailed,
        wait_for_response=wait
    )
    
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    if not wait:
        return TaskResponse(task_id=response["task_id"], status="processing")
    
    return SpamDetectionResponse(
        task_id=response["task_id"],
        status="completed",
        classification=response.get("classification", None),
        scores=response.get("scores", None),
        execution_time=response.get("execution_time", None),
        prediction_id=response.get("prediction_id", None)
    )

@app.post("/caption-image", response_model=ImageCaptionResponse)
async def caption_image(
    file: UploadFile = File(...),
    wait: bool = True,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
    producer: MLTaskProducer = Depends(get_task_producer)
):
    if not await check_user_balance(current_user, "image_caption", session):
        raise HTTPException(
            status_code=402,
            detail="Insufficient balance to perform this operation. Please add credits to your account."
        )
    
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    response = producer.send_image_caption_task(
        image_data=image_b64,
        user_id=current_user.id,
        wait_for_response=wait
    )
    
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    if not wait:
        return TaskResponse(task_id=response["task_id"], status="processing")
    
    return ImageCaptionResponse(
        task_id=response["task_id"],
        status="completed",
        caption=response.get("caption", None),
        execution_time=response.get("execution_time", None),
        prediction_id=response.get("prediction_id", None)
    )

@app.post("/payments/initiate", response_model=PaymentResponse)
async def initiate_payment(
    payment: PaymentRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    payment_id = str(uuid.uuid4())
    
    redirect_url = f"https://example.com/pay?payment_id={payment_id}&amount={payment.amount}"
    
    return PaymentResponse(
        payment_id=payment_id,
        status="pending",
        amount=payment.amount,
        redirect_url=redirect_url
    )

@app.get("/payments/callback")
async def payment_callback(
    payment_id: str,
    status: str,
    amount: int,
    signature: str,
    session: AsyncSession = Depends(get_session)
):
    user_id = 1
    
    if status == "completed":
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.balance += amount
            
            transaction = Transaction(
                user_id=user_id,
                change=amount,
                valid=True,
                time=datetime.now()
            )
            
            session.add(transaction)
            await session.commit()
            
            return {"status": "success", "message": "Payment processed successfully"}
    
    return {"status": "error", "message": "Payment processing failed"}

@app.post("/admin/update-balance/{user_id}")
async def update_user_balance(
    user_id: int,
    amount: int,
    admin_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(User).filter(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.balance += amount
    
    transaction = Transaction(
        user_id=user_id,
        change=amount,
        valid=True,
        time=datetime.now()
    )
    
    session.add(transaction)
    await session.commit()
    
    return {"user_id": user_id, "new_balance": user.balance}

@app.get("/balance")
async def get_user_balance(current_user: User = Depends(get_current_active_user)):
    return {"balance": current_user.balance}

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    import uuid
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("ml_api:app", host=host, port=port, reload=True) 