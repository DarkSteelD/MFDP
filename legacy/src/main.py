from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from src.database.init_db import init_db
from src.api.endpoints import users, balance, predictions
from src.api import ml_api

app = FastAPI(
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(balance.router, prefix="/users", tags=["balance"])
app.include_router(predictions.router, prefix="/ml", tags=["predictions"])
app.mount("/ml-tasks", ml_api.app, name="ml_tasks_api")

from src.api.auth import oauth2_scheme
app.include_router(users.router, tags=["auth"])

class Message(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize the database when the application starts."""
    await init_db()
    
    
@app.get("/", tags=["root"])
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "ML Course API is operational."}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint to verify the API is functioning properly."""
    return {"status": "ok"}

@app.get("/echo")
async def echo_get(message: str):
    return {"echo": message}

@app.post("/echo")
async def echo_post(msg: Message):
    return {"echo": msg.message}

@app.post("/echo/raw")
async def echo_raw(request: Request):
    body = await request.body()
    return {"echo_raw": body.decode("utf-8")}
