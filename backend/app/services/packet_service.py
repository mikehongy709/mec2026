from fastapi import HTTPException

from app.repositories.packet_repository import PacketRepository
from app.schemas.packets import MissionPacketIngest, PacketReceipt


class PacketService:
    def __init__(self, repository: PacketRepository):
        self.repository = repository

    def ingest(self, stream_id: str, packet: MissionPacketIngest) -> PacketReceipt:
        payload = packet.model_dump()
        stored, inserted = self.repository.store_once(stream_id, payload)
        if not inserted and stored.packet != payload:
            raise HTTPException(
                status_code=409,
                detail="This stream already has a different packet with that sequence number",
            )
        return PacketReceipt(
            id=stored.id,
            stream_id=stored.stream_id,
            seq=stored.seq,
            recorded_at=stored.recorded_at,
            duplicate=not inserted,
        )
