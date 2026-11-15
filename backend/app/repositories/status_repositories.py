from datetime import datetime

from sqlalchemy.orm import Session

from app.models.mission import MissionState, TelemetrySample


class MissionStatusRepository:
    """Loads the single persisted mission status used by the dashboard."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self) -> MissionState:
        mission = self.db.get(MissionState, 1)
        if mission is None:
            mission = MissionState(
                id=1,
                phase="orbit",
                link=True,
                checks={},
                telemetry={},
            )
            self.db.add(mission)
            self.db.flush()
        return mission

    def add_telemetry_sample(
        self,
        *,
        phase: str,
        link: bool,
        checks: dict[str, bool],
        readings: dict[str, float],
        recorded_at: datetime,
    ) -> TelemetrySample:
        sample = TelemetrySample(
            phase=phase,
            link=link,
            checks=checks,
            readings=readings,
            recorded_at=recorded_at,
        )
        self.db.add(sample)
        self.db.flush()
        return sample

    def get_latest_telemetry_sample(self) -> TelemetrySample | None:
        return (
            self.db.query(TelemetrySample)
            .order_by(TelemetrySample.id.desc())
            .first()
        )
