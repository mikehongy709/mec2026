from datetime import datetime

from fastapi import HTTPException

from app.models.mission import TelemetrySample
from app.repositories.status_repositories import MissionStatusRepository
from app.schemas.mission import DashboardResponse, Phase
from app.telemetry import METRIC_DEFINITIONS


PHASE_CHECKLISTS: dict[Phase, list[str]] = {
    "prelaunch": [
        "Fuel loaded and sealed",
        "Range safety cleared",
        "Crew suit checks complete",
        "Launch window confirmed",
    ],
    "ascent": [
        "Max-Q passed",
        "Stage separation confirmed",
        "Fairing jettison",
        "Orbital insertion burn",
    ],
    "orbit": [
        "Solar arrays deployed",
        "Antenna pointing verified",
        "Daily system diagnostics",
        "Crew exercise logged",
    ],
    "reentry": [
        "Deorbit burn planned",
        "Heat shield inspected",
        "Landing zone weather checked",
        "Recovery team on station",
    ],
}

LINK_DELAY_SECONDS = 1.3
TELEMETRY_STALE_AFTER_SECONDS = 3

class StatusService:
    def __init__(self, repository: MissionStatusRepository):
        self.repository = repository

    def get_dashboard(self) -> DashboardResponse:
        mission = self.repository.get_or_create()
        now = datetime.utcnow()
        latest_sample = self.repository.get_latest_telemetry_sample()
        telemetry_updated_at = latest_sample.recorded_at if latest_sample else None
        telemetry_stale = (
            not mission.link
            or telemetry_updated_at is None
            or (now - telemetry_updated_at).total_seconds() > TELEMETRY_STALE_AFTER_SECONDS
        )
        telemetry = mission.telemetry or {}
        metrics = []

        for definition in METRIC_DEFINITIONS:
            saved = telemetry.get(definition["id"], {})
            value = float(saved.get("value", definition["value"]))
            history = list(saved.get("history") or [value] * 30)

            metrics.append({**definition, "value": value, "history": history})

        return DashboardResponse(
            phase=mission.phase,
            link=mission.link,
            link_delay_seconds=LINK_DELAY_SECONDS,
            telemetry_stale=telemetry_stale,
            telemetry_updated_at=telemetry_updated_at,
            started_at=mission.started_at,
            elapsed_seconds=max(0, int((now - mission.started_at).total_seconds())),
            metrics=metrics,
            checklist_items=PHASE_CHECKLISTS[mission.phase],
            checks=mission.checks or {},
            updated_at=now,
        )

    def ingest_telemetry(self, readings: dict[str, float]) -> TelemetrySample:
        """Save one sample from the external generator and refresh the dashboard."""
        mission = self.repository.get_or_create()
        now = datetime.utcnow()
        displayed_telemetry = dict(mission.telemetry or {})
        for definition in METRIC_DEFINITIONS:
            metric_id = definition["id"]
            saved = displayed_telemetry.get(metric_id, {})
            displayed_value = float(saved.get("value", definition["value"]))
            history = list(saved.get("history") or [displayed_value] * 30)
            if mission.link:
                displayed_telemetry[metric_id] = {
                    "value": readings[metric_id],
                    "history": (history + [readings[metric_id]])[-30:],
                }

        # Store every received sample, but hold the last displayed value during
        # a simulated link outage.
        if mission.link:
            mission.telemetry = displayed_telemetry
        return self.repository.add_telemetry_sample(
            phase=mission.phase,
            link=mission.link,
            checks=dict(mission.checks or {}),
            readings=dict(readings),
            recorded_at=now,
        )

    def get_latest_telemetry(self) -> TelemetrySample:
        sample = self.repository.get_latest_telemetry_sample()
        if sample is None:
            raise HTTPException(status_code=404, detail="No telemetry samples have been received")
        return sample

    def set_phase(self, phase: Phase) -> DashboardResponse:
        mission = self.repository.get_or_create()
        mission.phase = phase
        return self.get_dashboard()

    def set_checklist_item(self, phase: Phase, item_index: int, checked: bool) -> DashboardResponse:
        if item_index >= len(PHASE_CHECKLISTS[phase]):
            raise HTTPException(status_code=422, detail="Checklist item does not exist")

        mission = self.repository.get_or_create()
        checks = dict(mission.checks or {})
        checks[f"{phase}:{item_index}"] = checked
        mission.checks = checks
        return self.get_dashboard()

    def set_link(self, link: bool) -> DashboardResponse:
        mission = self.repository.get_or_create()
        mission.link = link
        return self.get_dashboard()
