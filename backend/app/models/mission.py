from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String

from app.core.database import Base


class MissionState(Base):
    __tablename__ = "mission_state"

    id = Column(Integer, primary_key=True)
    phase = Column(String(20), nullable=False, default="orbit")
    link = Column(Boolean, nullable=False, default=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    checks = Column(JSON, nullable=False, default=dict)
    telemetry = Column(JSON, nullable=False, default=dict)
