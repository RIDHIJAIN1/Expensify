"""Upload stress tests: maximum file sizes, concurrent uploads, and limits.

Opt-in because they write hundreds of thousands of rows to the live database:

    RUN_STRESS=1 backend/.venv/Scripts/python.exe -m pytest integration_tests/test_upload_stress.py -q -s
"""

import importlib.util
import os
import threading
import time

import httpx
import pytest

from .conftest import (
    BASE_URL,
    FIXTURE_DIR,
    REPO_ROOT,
    logged_in_client,
    run_concurrently,
    timed,
)

pytestmark = pytest.mark.stress
MB = 1024 * 1024


def _generator():
    path = os.path.join(REPO_ROOT, "loadtests", "scripts", "generate_fixtures.py")
    spec = importlib.util.spec_from_file_location("fixture_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def large_fixtures():
    return _generator().generate_all(FIXTURE_DIR)


def _read(meta: dict) -> bytes:
    with open(meta["path"], "rb") as fh:
        return fh.read()


def _unique_csv(worker: int, rows: int) -> bytes:
    lines = ["Date,Description,Amount,Type,Reference\n"]
    for j in range(rows):
        lines.append(
            f"2026-09-{(j % 28) + 1:02d},BulkMerchant-{worker},"
            f"{100 + j}.{j % 100:02d},DEBIT,MED-{worker}-{j:06d}\n"
        )
    return "".join(lines).encode()


def test_single_max_size_upload(api, large_fixtures):
    meta = large_fixtures["max_upload"]
    content = _read(meta)
    assert len(content) < 10 * MB

    resp, ms = timed(lambda: api.upload(content, "max_upload.csv"))
    body = resp.json()
    print(
        f"\n[stress] single max upload: {len(content)/MB:.2f} MB, {meta['rows']} rows, "
        f"HTTP {resp.status_code}, imported={body.get('imported_count')}, "
        f"duplicates={body.get('duplicate_count')}, {ms:,.0f} ms "
        f"({meta['rows'] / (ms / 1000):,.0f} rows/s)"
    )
    assert resp.status_code == 201
    assert body["status"] == "COMPLETED"
    assert body["imported_count"] == meta["rows"]
    assert body["duplicate_count"] == 0
    assert body["error_summary"] is None
    assert api.get("/api/transactions", params={"limit": 1}).json()["total"] == meta["rows"]
    assert ms < 300_000


def test_over_limit_file_rejected(api, large_fixtures):
    meta = large_fixtures["over_limit"]
    content = _read(meta)
    assert len(content) > 10 * MB
    resp, ms = timed(lambda: api.upload(content, "over_limit.csv"))
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()
    assert ms < 15_000
    print(f"\n[stress] over-limit upload rejected in {ms:,.0f} ms")


def test_upload_over_row_limit_rejected(api, large_fixtures):
    meta = large_fixtures["rows_60k"]
    content = _read(meta)
    assert len(content) < 10 * MB
    resp, ms = timed(lambda: api.upload(content, "rows_60k.csv"))
    print(f"\n[stress] 60k-row upload -> HTTP {resp.status_code} in {ms:,.0f} ms")
    assert resp.status_code == 400


def test_concurrent_max_size_uploads(api, large_fixtures):
    meta = large_fixtures["max_upload"]
    content = _read(meta)
    workers = 4

    def upload(i):
        client = logged_in_client(api.email)
        try:
            resp, ms = timed(lambda: client.upload(content, f"max_concurrent_{i}.csv"))
            return resp, ms
        finally:
            client.close()

    started = time.perf_counter()
    responses = run_concurrently(upload, workers)
    wall_ms = (time.perf_counter() - started) * 1000

    statuses = [resp.status_code for resp, _ in responses]
    imported = sum(resp.json()["imported_count"] for resp, _ in responses)
    per_call = sorted(ms for _, ms in responses)
    print(
        f"\n[stress] {workers} concurrent max-size uploads of {len(content)/MB:.2f} MB each: "
        f"statuses={statuses}, imported={imported}, wall {wall_ms:,.0f} ms, "
        f"per-call min/median/max {per_call[0]:,.0f}/{per_call[len(per_call)//2]:,.0f}/{per_call[-1]:,.0f} ms"
    )
    assert all(status == 201 for status in statuses), statuses
    assert imported == meta["rows"], f"expected {meta['rows']} total imports, got {imported}"
    total = api.get("/api/transactions", params={"limit": 1}).json()["total"]
    assert total == meta["rows"]
    assert wall_ms < 900_000


def test_lightweight_requests_not_starved_by_max_upload(api, large_fixtures):
    meta = large_fixtures["max_upload"]
    content = _read(meta)
    upload_state: dict = {}

    def do_upload():
        client = logged_in_client(api.email)
        try:
            resp, ms = timed(lambda: client.upload(content, "blocking.csv"))
            upload_state["status"] = resp.status_code
            upload_state["ms"] = ms
        finally:
            client.close()

    uploader = threading.Thread(target=do_upload)
    uploader.start()
    time.sleep(0.5)

    latencies: list[float] = []
    probe = httpx.Client(base_url=BASE_URL, timeout=300)
    try:
        while uploader.is_alive():
            start = time.perf_counter()
            resp = probe.get("/api/health", timeout=300)
            latencies.append((time.perf_counter() - start) * 1000)
            assert resp.status_code == 200
            time.sleep(0.2)
    finally:
        probe.close()
    uploader.join(timeout=300)
    if not latencies:
        latencies.append(0.0)

    print(
        f"\n[stress] /api/health during max upload: probes={len(latencies)}, "
        f"max={max(latencies):,.0f} ms, avg={sum(latencies) / len(latencies):,.0f} ms, "
        f"upload took {upload_state.get('ms', 0):,.0f} ms"
    )
    assert upload_state.get("status") == 201
    assert max(latencies) < 5000, f"event loop starved health for {max(latencies):,.0f} ms"


def test_concurrent_medium_unique_uploads_import_everything(api):
    workers = 4
    rows_per_file = 10_000
    payloads = [_unique_csv(i, rows_per_file) for i in range(workers)]

    def upload(i):
        client = logged_in_client(api.email)
        try:
            resp, ms = timed(lambda: client.upload(payloads[i], f"medium_{i}.csv"))
            return resp, ms
        finally:
            client.close()

    started = time.perf_counter()
    responses = run_concurrently(upload, workers)
    wall_ms = (time.perf_counter() - started) * 1000

    imported = sum(resp.json()["imported_count"] for resp, _ in responses)
    print(
        f"\n[stress] {workers} concurrent {rows_per_file}-row uploads: "
        f"statuses={[resp.status_code for resp, _ in responses]}, imported={imported}, "
        f"wall {wall_ms:,.0f} ms, throughput {imported / (wall_ms / 1000):,.0f} rows/s"
    )
    assert all(resp.status_code == 201 for resp, _ in responses)
    assert imported == workers * rows_per_file
    assert api.get("/api/summary").json()["transaction_count"] == workers * rows_per_file
