from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_connect_args, get_database_url


def utcnow() -> datetime:
    """Naive UTC timestamp (avoids tzinfo mismatch with pg8000)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    future=True,
    connect_args=get_connect_args(),
)
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
