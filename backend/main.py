from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Engine, inspect, text

from app.api.v1.status import router as dashboard_router
from app.core.database import Base, engine
from app.models.mission import MissionState, TelemetrySample  # Register dashboard tables.


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
logger = logging.getLogger(__name__)


def upgrade_telemetry_archive_schema(database_engine: Engine = engine) -> None:
    columns = {
        column["name"]
        for column in inspect(database_engine).get_columns("telemetry_samples")
    }
    migrations = []
    if "link" not in columns:
        migrations.append(
            'ALTER TABLE telemetry_samples ADD COLUMN "link" BOOLEAN NOT NULL DEFAULT 1'
        )
    if "checks" not in columns:
        migrations.append(
            'ALTER TABLE telemetry_samples ADD COLUMN "checks" JSON NOT NULL DEFAULT \'{}\''
        )

    if migrations:
        with database_engine.begin() as connection:
            for statement in migrations:
                connection.execute(text(statement))


def create_app(database_engine: Engine | None = None) -> FastAPI:
    """Use the group's normal database, or an isolated database for tests."""
    selected_engine = database_engine if database_engine is not None else engine

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(bind=selected_engine)
        upgrade_telemetry_archive_schema(selected_engine)
        logger.info("Mission dashboard SQLite database: %s", selected_engine.url.database)
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
        # Rejected NaN/Infinity values cannot be echoed in a JSON error response.
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
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"]
    )
    application.include_router(dashboard_router, prefix="/api")
    application.mount(
        "/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend"
    )
    return application


app = create_app()
