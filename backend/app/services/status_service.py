import random
from datetime import datetime

from fastapi import HTTPException

from app.repositories.status_repositories import MissionStatusRepository
from app.schemas.mission import DashboardResponse, Phase


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

METRIC_DEFINITIONS = [
    {"id": "alt", "name": "Altitude", "unit": "km", "value": 408.0, "step": 0.4, "minimum": 395, "maximum": 420},
    {"id": "vel", "name": "Velocity", "unit": "km/s", "value": 7.66, "step": 0.01, "minimum": 7.5, "maximum": 7.8},
    {"id": "cab", "name": "Cabin pressure", "unit": "kPa", "value": 101.0, "step": 0.5, "minimum": 96, "maximum": 104},
    {"id": "pwr", "name": "Battery charge", "unit": "%", "value": 82.0, "step": 1.2, "minimum": 25, "maximum": 100},
    {"id": "tmp", "name": "Hull temperature", "unit": "°C", "value": 21.0, "step": 0.8, "minimum": -10, "maximum": 35},
    {"id": "o2", "name": "Oxygen reserve", "unit": "%", "value": 94.0, "step": 0.3, "minimum": 30, "maximum": 100},
]


class StatusService:
    def __init__(self, repository: MissionStatusRepository):
        self.repository = repository

    def get_dashboard(self, *, advance_telemetry: bool = True) -> DashboardResponse:
        mission = self.repository.get_or_create()
        now = datetime.utcnow()
        telemetry = dict(mission.telemetry or {})
        metrics = []

        for definition in METRIC_DEFINITIONS:
            saved = telemetry.get(definition["id"], {})
            value = float(saved.get("value", definition["value"]))
            history = list(saved.get("history", [value] * 30))

            # A dropped link holds the last reported values and history.
            if advance_telemetry and mission.link:
                value += (random.random() - 0.5) * 2 * definition["step"]
                history = (history + [value])[-30:]
                telemetry[definition["id"]] = {"value": value, "history": history}

            metrics.append({**definition, "value": value, "history": history})

        if advance_telemetry and mission.link:
            mission.telemetry = telemetry

        return DashboardResponse(
            phase=mission.phase,
            link=mission.link,
            link_delay_seconds=LINK_DELAY_SECONDS,
            started_at=mission.started_at,
            elapsed_seconds=max(0, int((now - mission.started_at).total_seconds())),
            metrics=metrics,
            checklist_items=PHASE_CHECKLISTS[mission.phase],
            checks=mission.checks or {},
            updated_at=now,
        )

    def set_phase(self, phase: Phase) -> DashboardResponse:
        mission = self.repository.get_or_create()
        mission.phase = phase
        return self.get_dashboard(advance_telemetry=False)

    def set_checklist_item(self, phase: Phase, item_index: int, checked: bool) -> DashboardResponse:
        if item_index >= len(PHASE_CHECKLISTS[phase]):
            raise HTTPException(status_code=422, detail="Checklist item does not exist")

        mission = self.repository.get_or_create()
        checks = dict(mission.checks or {})
        checks[f"{phase}:{item_index}"] = checked
        mission.checks = checks
        return self.get_dashboard(advance_telemetry=False)

    def set_link(self, link: bool) -> DashboardResponse:
        mission = self.repository.get_or_create()
        mission.link = link
        return self.get_dashboard(advance_telemetry=False)
