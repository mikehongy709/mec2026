from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.v1.status import router as dashboard_router
from app.core.database import Base, DATABASE_PATH, engine
from app.models.mission import MissionState, TelemetrySample  # Register dashboard tables.


PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
    Base.metadata.create_all(bind=engine)
    upgrade_telemetry_archive_schema()
    logger.info("Mission dashboard SQLite database: %s", DATABASE_PATH)
    yield


app = FastAPI(title="RemnantMonitor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"]
)

app.include_router(dashboard_router, prefix="/api")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
