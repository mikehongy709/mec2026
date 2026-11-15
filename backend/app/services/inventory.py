"""Derive shortage status from the stored mission-wide consumption rate."""

from ..models import Supply
from ..schemas import SupplyResponse


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
