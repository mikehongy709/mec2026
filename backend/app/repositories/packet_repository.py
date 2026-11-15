from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models.packet import MissionPacket


class PacketRepository:
    def __init__(self, db: Session):
        self.db = db

    def store_once(self, stream_id: str, packet: dict) -> tuple[MissionPacket, bool]:
        """Use SQLite uniqueness to protect concurrent retries, not a memory cache."""
        statement = (
            insert(MissionPacket)
            .values(stream_id=stream_id, seq=packet["seq"], packet=packet)
            .on_conflict_do_nothing(index_elements=["stream_id", "seq"])
        )
        inserted = self.db.execute(statement).rowcount == 1
        stored = self.db.execute(
            select(MissionPacket).where(
                MissionPacket.stream_id == stream_id,
                MissionPacket.seq == packet["seq"],
            )
        ).scalar_one()
        return stored, inserted
