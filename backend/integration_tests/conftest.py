"""Shared fixtures for live-server integration tests.

These tests hit a REAL running server (default http://127.0.0.1:8000) backed by
its real Postgres database. Each test gets its own freshly-created user so runs
are isolated from each other. Start the stack first:

    docker compose up -d
    backend/.venv/Scripts/python.exe -m pytest integration_tests -q
"""

import csv
import io
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

BASE_URL = os.environ.get("INTEGRATION_BASE_URL", "http://127.0.0.1:8000")
PASSWORD = "Int3gration!Pass"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAMPLE_CSV = os.path.join(REPO_ROOT, "sample_statement.csv")
FIXTURE_DIR = os.path.join(REPO_ROOT, "loadtests", "fixtures")


class Api:
    """Thin httpx wrapper that records per-call latency and the last response."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 300.0):
        self.client = httpx.Client(base_url=base_url, timeout=timeout)
        self.email: str | None = None

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        started = time.perf_counter()
        resp = self.client.request(method, path, **kwargs)
        resp.elapsed_ms = (time.perf_counter() - started) * 1000
        return resp

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def signup(self, email: str | None = None, name: str = "Integration") -> httpx.Response:
        self.email = email or f"it_{uuid.uuid4().hex[:10]}@example.com"
        return self.post(
            "/api/auth/signup",
            json={"email": self.email, "password": PASSWORD, "name": name},
        )

    def upload(self, content: bytes, filename: str = "statement.csv"):
        return self.post(
            "/api/uploads", files={"file": (filename, content, "text/csv")}
        )

    def categories_by_name(self) -> dict[str, int]:
        return {c["name"]: c["id"] for c in self.get("/api/categories").json()}

    def close(self) -> None:
        self.client.close()


def sample_csv_bytes() -> bytes:
    with open(SAMPLE_CSV, "rb") as fh:
        return fh.read()


def csv_rows(content: bytes) -> int:
    text = content.decode("utf-8", errors="ignore").strip().splitlines()
    return len([line for line in text if line.strip()]) - 1


def make_csv(rows: list[tuple]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Description", "Amount", "Type", "Reference"])
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def run_concurrently(fn, count: int, timeout: float = 600.0):
    with ThreadPoolExecutor(max_workers=count) as pool:
        futures = [pool.submit(fn, i) for i in range(count)]
        return [f.result(timeout=timeout) for f in futures]


def timed(fn):
    started = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - started) * 1000


def logged_in_client(email: str, password: str = PASSWORD) -> Api:
    client = Api()
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return client


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_STRESS") == "1":
        return
    skip = pytest.mark.skip(reason="stress tests are opt-in: set RUN_STRESS=1")
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session", autouse=True)
def server_ready():
    try:
        resp = httpx.get(f"{BASE_URL}/api/health", timeout=5)
        if resp.status_code != 200:
            pytest.exit(f"server unhealthy at {BASE_URL}: {resp.status_code}", returncode=1)
    except Exception as exc:  # noqa: BLE001
        pytest.exit(f"integration server not reachable at {BASE_URL}: {exc}", returncode=1)
    yield


@pytest.fixture()
def api(server_ready):
    a = Api()
    resp = a.signup()
    assert resp.status_code == 201, resp.text
    yield a
    a.close()


@pytest.fixture()
def api_with_data(api):
    content = sample_csv_bytes()
    resp = api.upload(content, "sample_statement.csv")
    assert resp.status_code == 201 and resp.json()["status"] == "COMPLETED", resp.text
    return api, resp.json()


@pytest.fixture()
def second_api(server_ready):
    a = Api()
    assert a.signup().status_code == 201
    yield a
    a.close()


@pytest.fixture(scope="session")
def sample_csv():
    return sample_csv_bytes()


@pytest.fixture(scope="session")
def sample_count():
    return csv_rows(sample_csv_bytes())
