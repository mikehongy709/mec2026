from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine

from app.api.v1.status import router as dashboard_router
from app.core.database import Base, engine
from app.models.mission import MissionState  # Register the dashboard model with SQLAlchemy.


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

def create_app(database_engine: Engine | None = None) -> FastAPI:
    """Use the normal database by default, or an isolated one for tests."""
    selected_engine = database_engine if database_engine is not None else engine

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        Base.metadata.create_all(bind=selected_engine)
        try:
            yield
        finally:
            selected_engine.dispose()

    application = FastAPI(
        title="RemnantMonitor API", version="1.0.0", lifespan=lifespan
    )
    application.state.database_engine = selected_engine

    @application.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, error: RequestValidationError):
        # NaN/Infinity in rejected input cannot be echoed in a JSON response.
        # Return the field and reason, so bad input stays a 422 instead of a 500.
        details = [
            {key: issue[key] for key in ("type", "loc", "msg")}
            for issue in error.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["null"],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["GET", "PUT"],
        allow_headers=["*"]
    )
    application.include_router(dashboard_router, prefix="/api")
    application.mount(
        "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
    )
    return application


app = create_app()
