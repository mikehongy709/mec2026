"""Validated inventory request and response formats."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


Quantity = Annotated[
    float,
    Field(strict=True, ge=0, le=1_000_000, allow_inf_nan=False),
]


class QuantityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Quantity


class SupplyResponse(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    id: str
    name: str
    unit: str
    quantity: float
    daily_consumption: float
    days_remaining: float | None
    status: Literal["healthy", "watch", "critical"]


class InventorySummary(BaseModel):
    total_supplies: int = Field(ge=0)
    healthy: int = Field(ge=0)
    watch: int = Field(ge=0)
    critical: int = Field(ge=0)
