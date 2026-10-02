import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

REQUIRED_HEADERS = ["Date", "Description", "Amount", "Type", "Reference"]

_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%Y",
]


class CSVError(Exception):
    """Fatal CSV problem (empty / unreadable / invalid header)."""


def _parse_date(value: str):
    value = (value or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid date: {value!r}")


def _parse_amount(value: str) -> Decimal:
    value = (value or "").strip()
    value = (
        value.replace("\u20b9", "")
        .replace("Rs", "").replace("rs", "").replace("RS", "")
        .replace(",", "").replace(" ", "")
    )
    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1]
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"invalid amount: {value!r}")
    return -amount if negative else amount


def _normalize_type(value: str) -> str:
    v = (value or "").strip().upper()
    if v in ("DEBIT", "DR", "DEB", "WITHDRAWAL", "PURCHASE", "PAYMENT"):
        return "DEBIT"
    if v in ("CREDIT", "CR", "DEPOSIT", "REFUND", "INCOME"):
        return "CREDIT"
    raise ValueError(f"invalid type: {value!r}")


def decode_bytes(data: bytes) -> str:
    if data.startswith(b"\xef\xbb\xbf"):  # strip UTF-8 BOM
        data = data[3:]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def parse_csv(data: bytes) -> tuple[list[dict], list[str]]:
    """Parse CSV bytes.

    Raises CSVError for fatal problems (empty / unreadable / invalid header).
    Returns (rows, errors) where `rows` are valid parsed transactions
    (date, description, amount, type, reference) and `errors` are per-row
    error strings that were skipped.
    """
    text = decode_bytes(data)
    try:
        reader = csv.reader(io.StringIO(text))
    except csv.Error as e:
        raise CSVError(f"cannot read file: {e}")

    header = next(reader, None)
    if header is None:
        raise CSVError("file is empty")
    fields = [f.strip().lower() for f in header]
    expected = [h.lower() for h in REQUIRED_HEADERS]
    if fields != expected:
        raise CSVError(f"invalid header. Expected {REQUIRED_HEADERS}, got {header}")

    rows: list[dict] = []
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        if not row or all((c or "").strip() == "" for c in row):
            continue  # skip blank lines
        if len(row) != len(REQUIRED_HEADERS):
            errors.append(f"row {i}: expected {len(REQUIRED_HEADERS)} columns, got {len(row)}")
            continue
        try:
            date = _parse_date(row[0])
            description = (row[1] or "").strip()
            if not description:
                raise ValueError("missing description")
            amount = _parse_amount(row[2])
            ttype = _normalize_type(row[3])
            reference = (row[4] or "").strip() or None
            rows.append({
                "date": date,
                "description": description,
                "amount": amount,
                "type": ttype,
                "reference": reference,
            })
        except Exception as e:
            errors.append(f"row {i}: {e}")

    return rows, errors
