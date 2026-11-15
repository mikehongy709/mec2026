from collections.abc import Iterator
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "app.db"
DATABASE_PATH = Path(os.environ.get("REMNANT_DB_PATH", DEFAULT_DATABASE_PATH)).resolve()
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
