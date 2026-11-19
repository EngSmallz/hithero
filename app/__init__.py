"""Lets `uvicorn app:app` keep working: re-exports the FastAPI app from app/main.py."""
from app.main import app