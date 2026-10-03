"""Migration full-cycle test: upgrade → downgrade → upgrade.

Runs against a dedicated throwaway database (expense_migration_test) so it
never touches the schema managed by conftest, and asserts the migrated schema
stays in sync with the SQLAlchemy models.
"""

import os

import pg8000
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app import models  # noqa: F401  (register tables on Base.metadata)
from app.config import settings
from app.database import Base

from .conftest import ADMIN_DB_URL

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")
MIGRATION_DB = "expense_migration_test"
MIGRATION_URL = (
    f"postgresql+pg8000://{ADMIN_DB_URL['user']}:{ADMIN_DB_URL['password']}"
    f"@{ADMIN_DB_URL['host']}:{ADMIN_DB_URL['port']}/{MIGRATION_DB}"
)
EXPECTED_TABLES = set(Base.metadata.tables)


def _admin(sql: str) -> None:
    conn = pg8000.connect(**ADMIN_DB_URL)
    conn.autocommit = True
    conn.cursor().execute(sql)
    conn.close()


def _alembic_config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


def _tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def _schema_diffs(engine) -> list:
    """Autogenerate diff: [] means migrations match the ORM models exactly."""
    with engine.connect() as conn:
        return compare_metadata(MigrationContext.configure(conn), Base.metadata)


def test_migration_upgrade_downgrade_upgrade(monkeypatch):
    _admin(f'DROP DATABASE IF EXISTS "{MIGRATION_DB}" WITH (FORCE)')
    _admin(f'CREATE DATABASE "{MIGRATION_DB}"')
    monkeypatch.setattr(settings, "DATABASE_URL", MIGRATION_URL)
    cfg = _alembic_config()
    engine = create_engine(MIGRATION_URL)

    try:
        command.upgrade(cfg, "head")
        assert _tables(engine) == EXPECTED_TABLES | {"alembic_version"}
        assert _schema_diffs(engine) == []

        command.downgrade(cfg, "base")
        assert _tables(engine) == {"alembic_version"}

        command.upgrade(cfg, "head")
        assert _tables(engine) == EXPECTED_TABLES | {"alembic_version"}
        assert _schema_diffs(engine) == []
    finally:
        engine.dispose()
        _admin(f'DROP DATABASE IF EXISTS "{MIGRATION_DB}" WITH (FORCE)')
