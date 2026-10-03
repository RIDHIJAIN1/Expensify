"""Integration tests for the export subsystem (CSV + PDF) against live data."""

import csv
import io
from decimal import Decimal

from .conftest import make_csv


def parse_csv_response(text: str) -> tuple[list[str], list[dict]]:
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    rows = [dict(zip(header, row)) for row in reader]
    return header, rows


def test_csv_export_matches_transactions_exactly(api_with_data, sample_count):
    api, _ = api_with_data
    resp = api.get("/api/export/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert resp.headers["content-disposition"] == "attachment; filename=transactions.csv"

    header, exported = parse_csv_response(resp.text)
    assert header == ["Date", "Description", "Amount", "Type", "Reference", "Category"]
    assert len(exported) == sample_count

    api_rows = api.get("/api/transactions", params={"limit": 1000}).json()["items"]
    assert len(api_rows) == len(exported)
    for api_row, csv_row in zip(api_rows, exported):
        assert csv_row["Date"] == api_row["date"]
        assert csv_row["Description"] == api_row["description"]
        assert csv_row["Type"] == api_row["type"]
        assert csv_row["Category"] == (api_row["category_name"] or "Uncategorized")
        assert csv_row["Reference"] == (api_row["reference"] or "")
        assert csv_row["Amount"] == f"{Decimal(str(api_row['amount'])):.2f}"
    dates = [row["Date"] for row in exported]
    assert dates == sorted(dates, reverse=True)


def test_csv_export_filters_match_api(api_with_data):
    api, _ = api_with_data
    params = {"date_from": "2026-09-01", "date_to": "2026-09-30", "type": "DEBIT"}
    exported = parse_csv_response(api.get("/api/export/csv", params=params).text)[1]
    api_rows = api.get("/api/transactions", params={**params, "limit": 1000}).json()["items"]
    assert len(exported) == len(api_rows) > 0
    assert all(row["Type"] == "DEBIT" for row in exported)
    assert all("2026-09-01" <= row["Date"] <= "2026-09-30" for row in exported)

    food = api.categories_by_name()["Food"]
    food_export = parse_csv_response(
        api.get("/api/export/csv", params={"category_id": food}).text
    )[1]
    assert food_export and all(row["Category"] == "Food" for row in food_export)

    junk = parse_csv_response(api.get("/api/export/csv", params={"category_id": 99999999}).text)
    assert junk[1] == []


def test_csv_export_escapes_tricky_text(api):
    rows = [
        ("2026-09-01", 'Amazon, Inc "Prime"', "100.00", "DEBIT", "UPI,1"),
        ("2026-09-02", "Café ₹ Mocha; Dosa", "80.00", "DEBIT", None),
    ]
    content = make_csv(rows)
    assert api.upload(content, "tricky.csv").json()["imported_count"] == 2

    header, exported = parse_csv_response(api.get("/api/export/csv").text)
    descriptions = {row["Description"] for row in exported}
    assert 'Amazon, Inc "Prime"' in descriptions
    assert "Café ₹ Mocha; Dosa" in descriptions
    refs = [row["Reference"] for row in exported]
    assert "UPI,1" in refs and "" in refs


def test_pdf_export_is_valid_and_filters_shrink_it(api_with_data):
    api, _ = api_with_data
    full = api.get("/api/export/pdf")
    assert full.status_code == 200
    assert full.headers["content-type"] == "application/pdf"
    assert full.headers["content-disposition"] == "attachment; filename=report.pdf"
    assert full.content[:5] == b"%PDF-"
    assert b"%%EOF" in full.content[-32:]
    assert len(full.content) > 1500

    filtered = api.get(
        "/api/export/pdf", params={"date_from": "2026-09-01", "date_to": "2026-09-30"}
    )
    assert filtered.status_code == 200
    assert filtered.content[:5] == b"%PDF-"
    assert len(filtered.content) < len(full.content)


def test_export_reflects_learning_end_to_end(api):
    content = make_csv([
        ("2026-09-01", "Chai Point", "120.00", "DEBIT", "CH-1"),
        ("2026-09-02", "Chai Point", "90.00", "DEBIT", "CH-2"),
    ])
    api.upload(content, "chai.csv")
    tx = api.get("/api/transactions", params={"search": "Chai", "limit": 10}).json()["items"][0]
    assert tx["category_name"] == "Other"

    food = api.categories_by_name()["Food"]
    learn = api.patch(f"/api/transactions/{tx['id']}", json={"category_id": food}).json()
    assert learn["learned_keyword"] == "chai point"
    assert learn["reclassified"] == 1

    exported = parse_csv_response(api.get("/api/export/csv").text)[1]
    chai_categories = {row["Category"] for row in exported if row["Description"] == "Chai Point"}
    assert chai_categories == {"Food"}

    summary = api.get("/api/summary").json()
    food_total = next(c for c in summary["by_category"] if c["category_name"] == "Food")
    assert Decimal(str(food_total["total"])) == Decimal("210.00")


def test_export_isolation_between_users(api_with_data, second_api):
    api, _ = api_with_data
    unique = api.get("/api/transactions", params={"limit": 1}).json()["items"][0]["description"]

    foreign = second_api.get("/api/export/csv")
    assert foreign.status_code == 200
    _, rows = parse_csv_response(foreign.text)
    assert rows == []

    foreign_pdf = second_api.get("/api/export/pdf")
    assert foreign_pdf.status_code == 200
    assert foreign_pdf.content[:5] == b"%PDF-"
    assert len(foreign_pdf.content) < len(api.get("/api/export/pdf").content)

    own = api.get("/api/export/csv").text
    assert unique in own


def test_export_empty_user_is_header_only(api):
    resp = api.get("/api/export/csv")
    assert resp.status_code == 200
    header, rows = parse_csv_response(resp.text)
    assert header[0] == "Date" and rows == []
