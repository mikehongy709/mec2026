"""Backward-compatible entry point; the FastAPI app lives in ``app.main``."""

from app.main import app

__all__ = ["app"]
