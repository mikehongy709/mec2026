"""Optional packet ingestion, independent of the existing dashboard API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.packet_repository import PacketRepository
from app.schemas.packets import MissionPacketIngest, PacketReceipt
from app.services.packet_service import PacketService


router = APIRouter(tags=["Mission packets"])


def get_packet_service(db: Session = Depends(get_db)) -> PacketService:
    return PacketService(PacketRepository(db))


@router.post(
    "/packet-streams/{stream_id}/packets",
    response_model=PacketReceipt,
    status_code=201,
    summary="Validate and store a simulator packet once per stream and sequence",
    responses={
        200: {"model": PacketReceipt, "description": "Identical packet already received"},
        409: {"description": "Sequence number already used for different data"},
    },
)
def ingest_packet(
    stream_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")],
    packet: MissionPacketIngest,
    response: Response,
    service: PacketService = Depends(get_packet_service),
):
    """Use a new stream ID for each run; replay packets with their original IDs."""
    receipt = service.ingest(stream_id, packet)
    if receipt.duplicate:
        response.status_code = 200
    return receipt
