"""
Module: routes.main

Contains the main page endpoint for the application.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the main page template with Jinja2.

    Steps:
      1. Serve an HTML page response displaying the ML service landing page.
      2. Include an overview of features: registration, authentication, balance management, predictions, and transaction history.
      3. Provide navigation links or buttons for each feature.

    Returns:
      HTMLResponse: rendered main page HTML content.

    Raises:
      None
    """
    return templates.TemplateResponse("main.html", {"request": request})