"""
Module: routes.main

Contains the main page endpoint for the application.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home():
    """
    Render the main page with a description of the ML service capabilities.

    Functional requirements:
      - Display an overview of ML service features.
      - Present navigation links or buttons for:
        - User registration and authentication.
        - Balance inquiry and top-up.
        - Prediction functionality.
        - Transaction history.
    """
    pass 