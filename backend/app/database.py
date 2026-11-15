"""SQLite storage and sample inventory. Existing quantities survive restarts."""

from collections.abc import Iterator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, URL, create_engine
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from .models import Base, Supply


# Quantities and consumption rates are mission-wide and match the frontend demo.
SAMPLE_SUPPLIES = (
    ("water", "Drinking water", "L", 192, 24),
    ("oxygen", "Oxygen", "kg", 72, 12),
    ("food", "Food rations", "meals", 324, 18),
    ("batteries", "Battery packs", "packs", 12, 4),
    ("filters", "CO₂ scrubber filters", "filters", 18, 1.5),
    ("medical", "Medical kits", "kits", 16, 0.2),
    ("fuel", "Rover fuel", "L", 180, 5),
    ("parts", "Spare components", "parts", 42, 0.4),
)


def build_engine(path: Path) -> Engine:
    return create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"check_same_thread": False},
    )


def initialize_inventory(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        for supply_id, name, unit, quantity, daily in SAMPLE_SUPPLIES:
            statement = insert(Supply).values(
                id=supply_id,
                name=name,
                unit=unit,
                quantity=quantity,
                daily_consumption=daily,
            ).on_conflict_do_nothing(index_elements=["id"])
            session.execute(statement)
        session.commit()


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
