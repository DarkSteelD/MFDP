"""
Main application entrypoint for the ML Service API.
"""

from fastapi import FastAPI

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

test_api.include_router(main_router)
test_api.include_router(auth_router)
test_api.include_router(balance_router)
test_api.include_router(transactions_router)
test_api.include_router(prediction_router)

test_api.alias = test_api
app = test_api 