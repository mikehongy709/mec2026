"""Separate packet archive; existing mission tables are not modified."""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Integer, JSON, String, UniqueConstraint

from app.database import Base


class MissionPacket(Base):
    __tablename__ = "mission_packets"
    __table_args__ = (UniqueConstraint("stream_id", "seq", name="uq_mission_packet_sequence"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stream_id = Column(String(64), nullable=False)
    seq = Column(BigInteger, nullable=False)
    recorded_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
    packet = Column(JSON, nullable=False)
