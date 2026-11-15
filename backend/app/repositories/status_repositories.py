from sqlalchemy.orm import Session

from app.models.mission import MissionState


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
