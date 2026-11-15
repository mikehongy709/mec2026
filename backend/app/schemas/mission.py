from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


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
