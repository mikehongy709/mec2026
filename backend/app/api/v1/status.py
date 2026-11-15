from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.status_repositories import MissionStatusRepository
from app.schemas.mission import (
    ChecklistUpdate,
    DashboardResponse,
    LinkUpdate,
    PhaseUpdate,
    TelemetryIngest,
    TelemetrySampleResponse,
)
from app.services.status_service import StatusService


router = APIRouter(tags=["Mission status"])


def get_status_service(db: Session = Depends(get_db)) -> StatusService:
    return StatusService(MissionStatusRepository(db))


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Read the current mission dashboard status",
)
def get_dashboard(service: StatusService = Depends(get_status_service)):
    """Return telemetry, mission clock, phase checklist, and communication state."""
    return service.get_dashboard()


@router.post(
    "/telemetry",
    response_model=TelemetrySampleResponse,
    status_code=201,
    summary="Store one telemetry sample from the data generator",
)
def ingest_telemetry(
    data: TelemetryIngest,
    service: StatusService = Depends(get_status_service),
):
    return service.ingest_telemetry(data.readings)


@router.get(
    "/telemetry/latest",
    response_model=TelemetrySampleResponse,
    summary="Read the latest stored telemetry sample",
)
def get_latest_telemetry(service: StatusService = Depends(get_status_service)):
    return service.get_latest_telemetry()


@router.put(
    "/phase",
    response_model=DashboardResponse,
    summary="Set the active mission phase",
)
def set_phase(data: PhaseUpdate, service: StatusService = Depends(get_status_service)):
    return service.set_phase(data.phase)


@router.put(
    "/checklist",
    response_model=DashboardResponse,
    summary="Update a mission checklist item",
)
def set_checklist_item(
    data: ChecklistUpdate,
    service: StatusService = Depends(get_status_service),
):
    return service.set_checklist_item(data.phase, data.item_index, data.checked)


@router.put(
    "/link",
    response_model=DashboardResponse,
    summary="Set the communication link state",
)
def set_link(data: LinkUpdate, service: StatusService = Depends(get_status_service)):
    return service.set_link(data.link)
