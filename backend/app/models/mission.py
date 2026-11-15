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


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    phase = Column(String(20), nullable=False)
    link = Column(Boolean, nullable=False)
    checks = Column(JSON, nullable=False)
    readings = Column(JSON, nullable=False)
