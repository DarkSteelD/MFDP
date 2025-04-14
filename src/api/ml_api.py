import os
import base64
import io
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.ml_task_producer import MLTaskProducer

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

class SpamDetectionResponse(TaskResponse):
    classification: Optional[str] = None
    scores: Optional[Dict[str, float]] = None

class ImageCaptionResponse(TaskResponse):
    caption: Optional[str] = None

def get_task_producer():
    producer = MLTaskProducer(RABBITMQ_URL, QUEUE_NAME)
    try:
        yield producer
    finally:
        producer.close()

@app.get("/")
async def root():
    return {"status": "ok", "message": "ML Service API is running"}

@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    request: TextGenerationRequest,
    background_tasks: BackgroundTasks,
    wait: bool = True,
    producer: MLTaskProducer = Depends(get_task_producer)
):
    """
    Generate text using a language model.
    
    Args:
        request: Text generation request
        background_tasks: FastAPI background tasks
        wait: Whether to wait for the task to complete
        producer: Task producer instance
        
    Returns:
        Task status or result
    """
    response = producer.send_text_generation_task(
        text=request.text,
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
        generated_text=response.get("generated_text", None)
    )

@app.post("/detect-spam", response_model=SpamDetectionResponse)
async def detect_spam(
    request: SpamDetectionRequest,
    background_tasks: BackgroundTasks,
    wait: bool = True,
    producer: MLTaskProducer = Depends(get_task_producer)
):
    response = producer.send_spam_detection_task(
        text=request.text,
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
        scores=response.get("scores", None)
    )

@app.post("/caption-image", response_model=ImageCaptionResponse)
async def caption_image(
    file: UploadFile = File(...),
    wait: bool = True,
    producer: MLTaskProducer = Depends(get_task_producer)
):
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    response = producer.send_image_caption_task(
        image_data=image_b64,
        wait_for_response=wait
    )
    
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
    
    if not wait:
        return TaskResponse(task_id=response["task_id"], status="processing")
    
    return ImageCaptionResponse(
        task_id=response["task_id"],
        status="completed",
        caption=response.get("caption", None)
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("ml_api:app", host=host, port=port, reload=True) 