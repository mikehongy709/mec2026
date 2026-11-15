"""Application entry point: uvicorn app.main:app --app-dir backend."""

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .database import build_engine, initialize_inventory
from .routes.inventory import router as inventory_router


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "remnant.db"


def create_app(database_path: str | Path | None = None) -> FastAPI:
    """Allow tests and local runs to use their own SQLite database file."""
    path = Path(
        database_path
        if database_path is not None
        else os.environ.get("REMNANT_DB_PATH", DEFAULT_DATABASE_PATH)
    ).resolve()
    engine = build_engine(path)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            initialize_inventory(engine)
            yield
        finally:
            engine.dispose()

    application = FastAPI(
        title="Remnant Inventory API",
        version="0.1.0",
        description="Update onboard quantities and calculate remaining supply days.",
        lifespan=lifespan,
    )
    application.state.engine = engine

    @application.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, error: RequestValidationError):
        # Invalid input can contain NaN/Infinity. Echoing those values in the
        # default error response causes JSON serialization to fail with HTTP 500.
        details = [
            {key: issue[key] for key in ("type", "loc", "msg")}
            for issue in error.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    application.include_router(inventory_router)
    return application


app = create_app()
