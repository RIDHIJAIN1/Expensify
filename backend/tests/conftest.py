import os

# Point the app at a dedicated test database BEFORE importing app modules.
os.environ["DATABASE_URL"] = "postgresql+pg8000://expense:expense@localhost:55432/expense_test"

import pg8000  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

ADMIN_DB_URL = {
    "user": "expense",
    "password": "expense",
    "host": "localhost",
    "port": 55432,
    "database": "expense",
}


def _ensure_test_db():
    conn = pg8000.connect(**ADMIN_DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'expense_test'")
    if cur.fetchone() is None:
        cur.execute("CREATE DATABASE expense_test")
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def _db():
    _ensure_test_db()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean(_db):
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def signup(client: TestClient, email: str, password: str = "supersecret1", name: str = "T"):
    return client.post(
        "/api/auth/signup", json={"email": email, "password": password, "name": name}
    )


SAMPLE_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "sample_statement.csv"
)


def sample_csv_bytes() -> bytes:
    with open(SAMPLE_CSV_PATH, "rb") as f:
        return f.read()


def sample_row_count() -> int:
    text = sample_csv_bytes().decode("utf-8", errors="ignore").strip().splitlines()
    return len([line for line in text if line.strip()]) - 1  # minus header
