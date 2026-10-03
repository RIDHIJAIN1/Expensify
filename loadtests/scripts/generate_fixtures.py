"""Generate large CSV fixtures for upload stress and k6 tests.

Usage:
    backend/.venv/Scripts/python.exe loadtests/scripts/generate_fixtures.py
"""

import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "loadtests", "fixtures")

MERCHANTS = ["Swiggy", "Zomato", "Amazon", "Uber", "Cult.fit", "PVR Cinemas",
             "BigBasket", "IRCTC", "Netflix", "Apollo Pharmacy"]
TYPES = ["DEBIT"] * 9 + ["CREDIT"]
MB = 1024 * 1024


def _row(n: int, pad: int = 0) -> str:
    month = n % 12 + 1
    day = n % 28 + 1
    cents = 1000 + n
    description = MERCHANTS[n % len(MERCHANTS)]
    if pad:
        description = f"{description} {'x' * pad}"
    return (
        f"2026-{month:02d}-{day:02d},"
        f"{description},"
        f"{cents // 100}.{cents % 100:02d},"
        f"{TYPES[n % len(TYPES)]},"
        f"FIX-{n:08d}\n"
    )


def generate_size(
    target_bytes: int, name: str, out_dir: str, max_rows: int | None = None, pad: int = 0
) -> dict:
    path = os.path.join(out_dir, name)
    header = "Date,Description,Amount,Type,Reference\n"
    size = len(header)
    rows = 0
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(header)
        while size < target_bytes and (max_rows is None or rows < max_rows):
            line = _row(rows, pad)
            fh.write(line)
            size += len(line)
            rows += 1
    return {"path": path, "bytes": os.path.getsize(path), "rows": rows}


def generate_rows(n_rows: int, name: str, out_dir: str) -> dict:
    path = os.path.join(out_dir, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("Date,Description,Amount,Type,Reference\n")
        for n in range(n_rows):
            fh.write(_row(n))
    return {"path": path, "bytes": os.path.getsize(path), "rows": n_rows}


def generate_all(out_dir: str = OUT_DIR) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    return {
        "medium_2mb": generate_size(2 * MB, "medium_2mb.csv", out_dir),
        # Near the 10 MB size cap but padded so the row count stays under the
        # 50k MAX_UPLOAD_ROWS limit (both caps must be exercisable together).
        "max_upload": generate_size(
            int(9.7 * MB), "max_upload.csv", out_dir, max_rows=49000, pad=150
        ),
        "over_limit": generate_size(10 * MB + 4096, "over_limit.csv", out_dir),
        "rows_60k": generate_rows(60000, "rows_60k.csv", out_dir),
    }


if __name__ == "__main__":
    summary = generate_all()
    for key, meta in summary.items():
        print(f"{key:>12}: {meta['bytes'] / MB:7.2f} MB  {meta['rows']:>7} rows  {meta['path']}")
    print(json.dumps(summary, indent=2))
