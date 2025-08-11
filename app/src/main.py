"""
Main application entrypoint for the ML Service API.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time
import logging

from src.core.database import init_db
from src.routes.main import router as main_router
from src.routes.auth import router as auth_router
from src.routes.balance import router as balance_router
from src.routes.transactions import router as transactions_router
from src.routes.prediction import router as prediction_router

logger = logging.getLogger(__name__)

test_api = FastAPI(
    title="ML Service API",
    description="API for user management, balance operations, and ML predictions",
    version="1.0.0"
)

# Defer DB initialization to startup, with retries to allow database container to be ready
@test_api.on_event("startup")
def startup_init_db() -> None:
    max_attempts = 10
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            init_db()
            logger.info("Database initialized successfully")
            return
        except Exception as exc:  # broad to catch DB not ready
            last_err = exc
            wait_s = min(5.0, 0.5 * (2 ** (attempt - 1)))
            logger.warning(f"Database init failed (attempt {attempt}/{max_attempts}): {exc}. Retrying in {wait_s}s...")
            time.sleep(wait_s)
    # If still failing after retries, raise to crash container (compose will restart)
    raise RuntimeError(f"Failed to initialize database after {max_attempts} attempts") from last_err

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