import pytest

from app.services.csv_parser import CSVError, parse_csv

VALID = "Date,Description,Amount,Type,Reference\n2026-09-01,Swiggy,428.50,DEBIT,UPI-1\n"


def test_valid_csv():
    rows, errors = parse_csv(VALID.encode())
    assert errors == []
    assert len(rows) == 1
    assert rows[0]["description"] == "Swiggy"
    assert rows[0]["type"] == "DEBIT"
    assert str(rows[0]["amount"]) == "428.50"


def test_invalid_header_raises():
    with pytest.raises(CSVError):
        parse_csv(b"Date,Name\n2026-09-01,Swiggy\n")


def test_empty_file_raises():
    with pytest.raises(CSVError):
        parse_csv(b"")


def test_bom_is_stripped():
    data = b"\xef\xbb\xbf" + VALID.encode()
    rows, errors = parse_csv(data)
    assert errors == []
    assert len(rows) == 1


def test_bad_rows_are_skipped_and_reported():
    data = (
        "Date,Description,Amount,Type,Reference\n"
        "2026-09-01,Swiggy,428.50,DEBIT,UPI-1\n"
        "not-a-date,Bad,99,DEBIT,X\n"
    ).encode()
    rows, errors = parse_csv(data)
    assert len(rows) == 1
    assert len(errors) == 1
    assert "row 3" in errors[0]


def test_amount_with_currency_symbol():
    data = "Date,Description,Amount,Type,Reference\n2026-09-01,Coffee,₹120.50,DEBIT,X\n".encode()
    rows, _ = parse_csv(data)
    assert str(rows[0]["amount"]) == "120.50"


def test_latin1_fallback():
    # "café" encoded in latin-1 should still parse (decode fallback)
    data = "Date,Description,Amount,Type,Reference\n2026-09-01,café,120.50,DEBIT,X\n".encode("latin-1")
    rows, errors = parse_csv(data)
    assert len(rows) == 1
