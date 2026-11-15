from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.telemetry import METRIC_IDS


Phase = Literal["prelaunch", "ascent", "orbit", "reentry"]


class Metric(BaseModel):
    id: str
    name: str
    unit: str
    value: float
    step: float
    minimum: float
    maximum: float
    history: list[float]


class DashboardResponse(BaseModel):
    phase: Phase
    link: bool
    link_delay_seconds: float
    started_at: datetime
    elapsed_seconds: int
    metrics: list[Metric]
    checklist_items: list[str]
    checks: dict[str, bool]
    updated_at: datetime


class PhaseUpdate(BaseModel):
    phase: Phase


class ChecklistUpdate(BaseModel):
    phase: Phase
    item_index: int = Field(ge=0)
    checked: bool


class LinkUpdate(BaseModel):
    link: bool


class TelemetryIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readings: dict[str, Annotated[float, Field(allow_inf_nan=False)]]

    @field_validator("readings")
    @classmethod
    def validate_reading_ids(cls, readings: dict[str, float]) -> dict[str, float]:
        if set(readings) != METRIC_IDS:
            raise ValueError("Readings must include exactly the supported metric IDs")
        return readings


class TelemetrySampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    phase: Phase
    link: bool
    checks: dict[str, bool]
    readings: dict[str, float]
