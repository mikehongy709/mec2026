"""The RemnantMonitor FastAPI application."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.v1.packets import router as packet_router
from app.api.v1.status import router as status_router
from app.database import Base, DATABASE_PATH, engine
from app.models.mission import MissionState, TelemetrySample  # Register tables.


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
logger = logging.getLogger(__name__)


def upgrade_telemetry_archive_schema() -> None:
    columns = {
        column["name"]
        for column in inspect(engine).get_columns("telemetry_samples")
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
        with engine.begin() as connection:
            for statement in migrations:
                connection.execute(text(statement))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    upgrade_telemetry_archive_schema()
    logger.info("Mission dashboard SQLite database: %s", DATABASE_PATH)
    yield


app = FastAPI(
    title="RemnantMonitor API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, error: RequestValidationError):
    # Do not echo rejected NaN/Infinity values, which would break JSON encoding.
    details = [
        {key: issue[key] for key in ("type", "loc", "msg")}
        for issue in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

app.include_router(status_router, prefix="/api")
app.include_router(packet_router, prefix="/api")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
