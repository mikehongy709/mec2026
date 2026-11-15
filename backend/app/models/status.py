from sqlalchemy import Column, ForeignKey, Integer, String, Double

from sqlalchemy import DateTime
from datetime import datetime

from sqlalchemy.orm import relationship

from app.core.database import Base


class Status(Base):

    __tablename__ = "status"

    id = Column(Integer, primary_key=True)

    temp = Column(Double , nullable=False)

    height = Column(Double, nullable=False)

    speed = Column(Double, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    
