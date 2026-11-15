"""Derive inventory views from the current stored quantities and consumption."""

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Supply
from ..schemas import InventorySummary, SupplyResponse


def describe_supply(supply: Supply) -> SupplyResponse:
    # JSON has no Infinity value; null means there is no ongoing consumption.
    days = (
        supply.quantity / supply.daily_consumption
        if supply.daily_consumption > 0
        else None
    )
    if days is not None and days <= 3:
        status = "critical"
    elif days is not None and days <= 7:
        status = "watch"
    else:
        status = "healthy"

    return SupplyResponse(
        id=supply.id,
        name=supply.name,
        unit=supply.unit,
        quantity=supply.quantity,
        daily_consumption=supply.daily_consumption,
        days_remaining=days,
        status=status,
    )


def list_supplies(session: Session) -> list[SupplyResponse]:
    supplies = session.scalars(select(Supply).order_by(Supply.id)).all()
    return [describe_supply(supply) for supply in supplies]


def summarize_inventory(supplies: list[SupplyResponse]) -> InventorySummary:
    counts = Counter(supply.status for supply in supplies)
    return InventorySummary(
        total_supplies=len(supplies),
        healthy=counts["healthy"],
        watch=counts["watch"],
        critical=counts["critical"],
    )


def shortage_alerts(supplies: list[SupplyResponse]) -> list[SupplyResponse]:
    alerts = [supply for supply in supplies if supply.status in ("critical", "watch")]
    return sorted(
        alerts,
        key=lambda supply: (
            supply.days_remaining if supply.days_remaining is not None else float("inf"),
            supply.id,
        ),
    )
