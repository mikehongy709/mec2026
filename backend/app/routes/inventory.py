"""Read a supply or set its onboard quantity."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Supply
from ..schemas import QuantityUpdate, SupplyResponse
from ..services.inventory import describe_supply


router = APIRouter(prefix="/api/inventory", tags=["Inventory"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def find_supply(supply_id: str, session: Session) -> Supply:
    supply = session.get(Supply, supply_id)
    if supply is None:
        raise HTTPException(status_code=404, detail="Supply not found")
    return supply


@router.get("/{supply_id}", response_model=SupplyResponse)
def read_supply(supply_id: str, session: DatabaseSession) -> SupplyResponse:
    """Inspect the current quantity, remaining days, and shortage status."""
    return describe_supply(find_supply(supply_id, session))


@router.patch("/{supply_id}", response_model=SupplyResponse)
def update_quantity(
    supply_id: str, update: QuantityUpdate, session: DatabaseSession
) -> SupplyResponse:
    """Set an absolute quantity; consumption rate and units remain unchanged."""
    supply = find_supply(supply_id, session)
    supply.quantity = update.quantity
    session.commit()
    session.refresh(supply)
    return describe_supply(supply)
