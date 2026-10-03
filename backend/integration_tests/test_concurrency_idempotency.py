"""Concurrency and idempotency behaviour of the live API.

Each test spins up its own user so there is no cross-test interference. Threads
use separate HTTP clients (and therefore separate connections/cookies) to
exercise real parallelism in the server's threadpool/event loop.
"""

import threading
import time
from collections import Counter

from .conftest import (
    Api,
    logged_in_client,
    make_csv,
    run_concurrently,
    timed,
)


def test_sequential_reupload_is_idempotent(api, sample_csv, sample_count):
    first = api.upload(sample_csv).json()
    second = api.upload(sample_csv).json()
    third = api.upload(sample_csv).json()
    assert first["imported_count"] == sample_count
    for repeat in (second, third):
        assert repeat["imported_count"] == 0
        assert repeat["duplicate_count"] == sample_count
    assert api.get("/api/transactions", params={"limit": 1}).json()["total"] == sample_count
    assert len(api.get("/api/uploads").json()) == 3


def test_repeated_patch_is_idempotent(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    food = api.categories_by_name()["Food"]

    first = api.patch(f"/api/transactions/{tx['id']}", json={"category_id": food}).json()
    assert first["learned_keyword"] is not None
    learned = first["learned_keyword"]

    second = api.patch(f"/api/transactions/{tx['id']}", json={"category_id": food}).json()
    assert second["learned_keyword"] is None
    assert second["reclassified"] == 0
    assert second["transaction"]["category_id"] == food

    keywords = [k for c in api.get("/api/categories").json() if c["name"] == "Food" for k in c["keywords"]]
    assert keywords.count(learned) == 1


def test_repeated_budget_put_and_delete_are_idempotent(api_with_data):
    api, _ = api_with_data
    food = api.categories_by_name()["Food"]
    first = api.put(f"/api/budgets/{food}", json={"amount": "1500.00"})
    second = api.put(f"/api/budgets/{food}", json={"amount": "1500.00"})
    assert first.status_code == second.status_code == 200
    assert first.json()["limit"] == second.json()["limit"] == "1500.00"
    assert len(api.get("/api/budgets").json()) == 1
    assert api.delete(f"/api/budgets/{food}").status_code == 200
    assert api.delete(f"/api/budgets/{food}").status_code == 404


def test_logout_and_refresh_are_idempotent(server_ready):
    a = Api()
    try:
        a.signup()
        assert a.post("/api/auth/logout").status_code == 200
        assert a.post("/api/auth/logout").status_code == 200
        assert a.post("/api/auth/refresh").status_code == 401

        assert a.post("/api/auth/login", json={"email": a.email, "password": "Int3gration!Pass"}).status_code == 200
        assert a.post("/api/auth/refresh").status_code == 200
        assert a.post("/api/auth/refresh").status_code == 200
        assert a.get("/api/auth/me").status_code == 200
    finally:
        a.close()


def test_concurrent_identical_uploads_import_once(api, sample_csv, sample_count):
    email = api.email
    workers = 5

    def upload(i):
        client = logged_in_client(email)
        try:
            return client.upload(sample_csv, f"same_{i}.csv")
        finally:
            client.close()

    responses = run_concurrently(upload, workers)
    statuses = Counter(r.status_code for r in responses)
    assert set(statuses) == {201}, [r.text for r in responses if r.status_code != 201]

    imported = sum(r.json()["imported_count"] for r in responses)
    duplicated = sum(r.json()["duplicate_count"] for r in responses)
    assert imported == sample_count, f"concurrent duplicate imports: {imported} vs {sample_count}"
    assert duplicated == (workers - 1) * sample_count

    assert api.get("/api/transactions", params={"limit": 1}).json()["total"] == sample_count
    uploads = api.get("/api/uploads").json()
    assert len(uploads) == workers
    assert sorted(u["imported_count"] for u in uploads) == [0] * (workers - 1) + [sample_count]


def test_concurrent_distinct_uploads_all_import(api):
    email = api.email
    workers = 4
    rows_per_file = 40

    def upload(i):
        rows = [
            ("2026-09-01", f"Merchant-{i}", f"{100 + j}.00", "DEBIT", f"CONC-{i}-{j}")
            for j in range(rows_per_file)
        ]
        client = logged_in_client(email)
        try:
            return client.upload(make_csv(rows), f"distinct_{i}.csv")
        finally:
            client.close()

    responses = run_concurrently(upload, workers)
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    assert sum(r.json()["imported_count"] for r in responses) == workers * rows_per_file
    total = api.get("/api/transactions", params={"limit": 1}).json()["total"]
    assert total == workers * rows_per_file
    assert api.get("/api/summary").json()["transaction_count"] == workers * rows_per_file


def test_concurrent_signup_same_email_exactly_one(server_ready):
    import uuid

    email = f"race_{uuid.uuid4().hex[:10]}@example.com"

    def signup(i):
        client = Api()
        try:
            return client.post(
                "/api/auth/signup",
                json={"email": email, "password": "Int3gration!Pass", "name": f"W{i}"},
            )
        finally:
            client.close()

    responses = run_concurrently(signup, 8)
    codes = Counter(r.status_code for r in responses)
    assert codes[201] == 1, f"expected exactly one account, got {dict(codes)}"
    assert codes[400] == 7, f"expected seven duplicate-email 400s, got {dict(codes)}"
    assert not any(code >= 500 for code in codes)


def test_concurrent_category_create_same_name(api):
    def create(i):
        return api.post("/api/categories", json={"name": "RaceCat", "keywords": []})

    responses = run_concurrently(create, 8)
    codes = Counter(r.status_code for r in responses)
    assert codes[201] == 1, f"duplicate category created concurrently: {dict(codes)}"
    assert codes[400] == 7, f"expected duplicate-name 400s, got {dict(codes)}"
    assert not any(code >= 500 for code in codes)
    names = [c["name"] for c in api.get("/api/categories").json()]
    assert names.count("RaceCat") == 1


def test_concurrent_budget_put_leaves_single_row(api_with_data):
    api, _ = api_with_data
    workers = 12
    rounds = 3
    failures: dict[int, dict] = {}

    for round_no in range(rounds):
        cat_id = api.post(
            "/api/categories", json={"name": f"RaceBudget{round_no}", "keywords": []}
        ).json()["id"]

        def put(i, cat=cat_id, r=round_no):
            return api.put(f"/api/budgets/{cat}", json={"amount": f"{1000 + i * 250 + r}.00"})

        responses = run_concurrently(put, workers)
        codes = Counter(r.status_code for r in responses)
        if codes.get(200) != workers:
            failures[round_no] = dict(codes)

        owned = [b for b in api.get("/api/budgets").json() if b["category_id"] == cat_id]
        assert len(owned) == 1, f"round {round_no}: expected one budget row, got {len(owned)}"

    assert not failures, f"non-200 during concurrent budget upsert: {failures}"


def test_concurrent_patch_same_transaction(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    cats = [
        api.post("/api/categories", json={"name": f"Race{i}", "keywords": []}).json()["id"]
        for i in range(2)
    ]

    def patch(i):
        return api.patch(
            f"/api/transactions/{tx['id']}", json={"category_id": cats[i % 2]}
        )

    responses = run_concurrently(patch, 8)
    codes = Counter(r.status_code for r in responses)
    assert codes[200] == 8, f"non-200 during concurrent patch: {dict(codes)}"
    final = api.get(f"/api/transactions/{tx['id']}").json()
    assert final["category_id"] in cats


def test_reads_stay_healthy_while_large_upload_runs(api):
    rows = [
        ("2026-09-20", f"Bulk Vendor {i % 50}", f"{i % 900 + 1}.00", "DEBIT", f"BULK-{i}")
        for i in range(4000)
    ]
    content = make_csv(rows)

    upload_result: dict = {}

    def do_upload():
        client = logged_in_client(api.email)
        try:
            started = time.perf_counter()
            resp = client.upload(content, "bulk.csv")
            upload_result["status"] = resp.status_code
            upload_result["ms"] = (time.perf_counter() - started) * 1000
        finally:
            client.close()

    stop = threading.Event()
    read_latencies: list[float] = []
    read_statuses: list[int] = []

    def read_loop():
        client = logged_in_client(api.email)
        try:
            while not stop.is_set():
                resp, ms = timed(lambda: client.get("/api/summary"))
                read_statuses.append(resp.status_code)
                read_latencies.append(ms)
                time.sleep(0.05)
        finally:
            client.close()

    reader = threading.Thread(target=read_loop)
    uploader = threading.Thread(target=do_upload)
    reader.start()
    time.sleep(0.2)
    uploader.start()
    uploader.join(timeout=300)
    stop.set()
    reader.join(timeout=30)

    assert upload_result["status"] == 201
    assert read_statuses and all(code == 200 for code in read_statuses)
    assert max(read_latencies) < 30000


def test_parallel_same_transaction_patch_and_summary_never_500(api_with_data):
    api, _ = api_with_data
    tx = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]
    food = api.categories_by_name()["Food"]

    def call(i):
        if i % 3 == 0:
            return api.patch(f"/api/transactions/{tx['id']}", json={"category_id": food})
        if i % 3 == 1:
            return api.get("/api/summary")
        return api.get("/api/transactions", params={"limit": 20})

    responses = run_concurrently(call, 30)
    assert all(r.status_code == 200 for r in responses)
