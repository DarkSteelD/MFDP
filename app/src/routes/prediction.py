"""
Module: routes.prediction

Contains endpoints for ML prediction operations.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import base64
import os
import shutil
from pathlib import Path
from aio_pika import connect_robust, Message

from src.schemas.prediction import PredictionRequest, PredictionResponse, Scan3DResponse
from src.dependencies import get_db, get_current_active_user
from src.db.models import User as DBUser, Transaction

router = APIRouter(prefix="/predict", tags=["prediction"])

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
IMAGE_QUEUE = os.getenv("IMAGE_QUEUE", "image_tasks")
SCAN3D_QUEUE = os.getenv("SCAN3D_QUEUE", "scan3d_tasks")

@router.post("/", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    # Validate base64 image
    try:
        base64.b64decode(request.image)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image data")

    # Ensure positive balance
    if current_user.balance <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    # Charge fixed credits for prediction
    credits_spent = 50.0

    # Create a 'prediction' transaction record and deduct balance
    transaction = Transaction(
        user_id=current_user.id,
        type="prediction",
        amount=credits_spent
    )
    db.add(transaction)
    current_user.balance -= credits_spent
    db.add(current_user)
    db.commit()

    # Publish task to RabbitMQ; on connection failure, raise 500 for this API
    try:
        connection = await connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(body=base64.b64encode(b"prediction task")), routing_key=IMAGE_QUEUE
        )
        await connection.close()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Messaging backend unavailable")

    # Return mock mask URL
    mask_url = f"/downloads/mask_{current_user.id}_image.png"
    return PredictionResponse(image_prediction=mask_url, credits_spent=credits_spent)


@router.post("/3d-scan", response_model=Scan3DResponse)
async def predict_3d_scan(
    scan: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_active_user)
):
    # Validate file format
    filename = scan.filename or "scan.nii.gz"
    if not (filename.endswith(".nii") or filename.endswith(".nii.gz")):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a NIfTI file (.nii or .nii.gz)")

    # Ensure positive balance
    if current_user.balance <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    uploads_dir = Path("uploads")
    downloads_dir = Path("downloads")
    uploads_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)

    # Save uploaded file
    saved_name = f"{current_user.id}_{filename}"
    upload_path = uploads_dir / saved_name
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(scan.file, f)

    # Charge fixed credits for 3D scan analysis
    credits_spent = 100.0

    # Create a 'scan3d' transaction and deduct balance
    transaction = Transaction(
        user_id=current_user.id,
        type="scan3d",
        amount=credits_spent
    )
    db.add(transaction)
    current_user.balance -= credits_spent
    db.add(current_user)
    db.commit()

    # Generate placeholder masks by copying the original upload
    brain_mask_name = f"brain_mask_{current_user.id}_{filename}"
    aneurysm_mask_name = f"aneurysm_mask_{current_user.id}_{filename}"
    brain_mask_path = downloads_dir / brain_mask_name
    aneurysm_mask_path = downloads_dir / aneurysm_mask_name

    try:
        shutil.copyfile(upload_path, brain_mask_path)
        shutil.copyfile(upload_path, aneurysm_mask_path)
    except Exception:
        # If copy fails, still return URLs; frontend will handle 404 if not present
        pass

    # Optionally publish a task to RabbitMQ (best-effort)
    try:
        connection = await connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        await channel.default_exchange.publish(
            Message(body=f"scan3d task for {saved_name}".encode()), routing_key=SCAN3D_QUEUE
        )
        await connection.close()
    except Exception:
        # Ignore messaging failure for synchronous API response
        pass

    return Scan3DResponse(
        brain_mask_url=f"/downloads/{brain_mask_name}",
        aneurysm_mask_url=f"/downloads/{aneurysm_mask_name}",
        original_scan_url=saved_name,
        credits_spent=credits_spent
    )