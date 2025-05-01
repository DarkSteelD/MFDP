"""
Module: core.config

Holds configuration variables loaded from environment.
"""

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# JWT settings
SECRET_KEY: str = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))