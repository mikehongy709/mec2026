"""Packet contract matching the group's browser simulator."""

from datetime import datetime
from math import floor, isfinite
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


MAX_SAFE_INTEGER = 2**53 - 1
CHECKSUM_MODULUS = 65521
FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]


def packet_checksum(packet: "MissionPacketIngest") -> int:
    """Match the browser's Math.round(sum) % 65521, including negative values."""
    total = (
        packet.alt * 10
        + packet.vel * 1000
        + packet.g * 100
        + packet.tmp * 10
        + packet.pwr * 10
        + packet.prs * 10
        + packet.seq
    )
    if not isfinite(total) or abs(total) > MAX_SAFE_INTEGER:
        raise ValueError("Packet values exceed the checksum's safe numeric range")
    # Python round() uses ties-to-even; JavaScript rounds ties toward +infinity.
    rounded = floor(total)
    if total - rounded >= 0.5:
        rounded += 1
    # JavaScript's remainder keeps the dividend's sign, unlike Python modulo.
    return rounded % CHECKSUM_MODULUS if rounded >= 0 else -(-rounded % CHECKSUM_MODULUS)


class MissionPacketIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alt: FiniteNumber = Field(ge=0)
    vel: FiniteNumber = Field(ge=0)
    g: FiniteNumber
    tmp: FiniteNumber
    pwr: FiniteNumber = Field(ge=0, le=100)
    prs: FiniteNumber = Field(ge=0)
    seq: Annotated[int, Field(strict=True, ge=0, le=MAX_SAFE_INTEGER)]
    crc: Annotated[int, Field(strict=True, ge=-(CHECKSUM_MODULUS - 1), lt=CHECKSUM_MODULUS)]

    @model_validator(mode="after")
    def validate_checksum(self) -> "MissionPacketIngest":
        if self.crc != packet_checksum(self):
            raise ValueError("Packet checksum does not match its readings and sequence")
        return self


class PacketReceipt(BaseModel):
    id: int
    stream_id: str
    seq: int
    recorded_at: datetime
    duplicate: bool
