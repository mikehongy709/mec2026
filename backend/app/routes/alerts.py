"""Current shortages, calculated on request rather than saved as stale alerts."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..schemas import SupplyResponse
from ..services.inventory import list_supplies, shortage_alerts


router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=list[SupplyResponse])
def read_alerts(
    session: Annotated[Session, Depends(get_session)],
) -> list[SupplyResponse]:
    """Return critical and watch supplies, ordered by remaining days then ID."""
    return shortage_alerts(list_supplies(session))
