import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import get_connect_args, get_database_url


def utcnow() -> datetime:
    """Naive UTC timestamp (avoids tzinfo mismatch with pg8000)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Serverless (Vercel) spawns many short-lived instances: don't hoard connections.
_pool_kwargs = {"poolclass": NullPool} if os.environ.get("VERCEL") else {}

engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    future=True,
    connect_args=get_connect_args(),
    **_pool_kwargs,
)
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


@contextmanager
def transaction(db: Session) -> Iterator[Session]:
    """Unit of work: commit on success, rollback on any failure."""
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
