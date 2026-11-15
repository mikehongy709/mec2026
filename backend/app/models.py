"""Persisted inventory fields. Remaining days and status are calculated on read."""

from sqlalchemy import CheckConstraint, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Supply(Base):
    __tablename__ = "supplies"
    __table_args__ = (
        CheckConstraint("quantity >= 0 AND quantity <= 1000000"),
        CheckConstraint("daily_consumption >= 0"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[float] = mapped_column(Float)
    daily_consumption: Mapped[float] = mapped_column(Float)
