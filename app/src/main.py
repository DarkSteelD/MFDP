"""
Main application entrypoint for the ML Service API.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.core.database import init_db
from src.routes.main import router as main_router
from src.routes.auth import router as auth_router
from src.routes.balance import router as balance_router
from src.routes.transactions import router as transactions_router
from src.routes.prediction import router as prediction_router

test_api = FastAPI(
    title="ML Service API",
    description="API for user management, balance operations, and ML predictions",
    version="1.0.0"
)

init_db()

# Mount static files for uploads and downloads
uploads_dir = Path("uploads")
downloads_dir = Path("downloads")
uploads_dir.mkdir(exist_ok=True)
downloads_dir.mkdir(exist_ok=True)

test_api.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
test_api.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

test_api.include_router(main_router)
test_api.include_router(auth_router)
test_api.include_router(balance_router)
test_api.include_router(transactions_router)
test_api.include_router(prediction_router)

test_api.alias = test_api
app = test_api 