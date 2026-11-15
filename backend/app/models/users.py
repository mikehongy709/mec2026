from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy import DateTime
from datetime import datetime

from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String(30), nullable=False)

    email = Column(String(255), unique=True, nullable=False)

    password = Column(String, nullable=False)

    avatar_url = Column(
        String,
        nullable=True
    )

    bio = Column(
        String(500),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    videos = relationship(
        "Video",
        back_populates="owner",
        cascade="all, delete-orphan"
    )