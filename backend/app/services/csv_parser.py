import csv
import io
from datetime import datetime, date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

REQUIRED_HEADERS = ["Date", "Description", "Amount", "Type", "Reference"]

# Must match the DB columns exactly so nothing oversized reaches Postgres.
DESCRIPTION_MAX = 500
REFERENCE_MAX = 200
AMOUNT_MAX = Decimal("9999999999.99")  # numeric(12, 2)
AMOUNT_QUANTUM = Decimal("0.01")
EARLIEST_DATE = date(1900, 1, 1)
LATEST_DATE = date(2100, 12, 31)

_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y",
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%Y",
]


class CSVError(Exception):
    """Fatal CSV problem (empty / unreadable / invalid header)."""


def _parse_date(value: str) -> date:
    raw = (value or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt).date()
            if not (EARLIEST_DATE <= parsed <= LATEST_DATE):
                break
            return parsed
        except ValueError:
            continue
    raise ValueError(f"invalid date: {raw!r}")


def _parse_amount(value: str) -> Decimal:
    raw = (value or "").strip()
    cleaned = (
        raw.replace("\u20b9", "")
        .replace("Rs", "").replace("rs", "").replace("RS", "")
        .replace(",", "").replace(" ", "")
    )
    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1]
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"invalid amount: {raw!r}")
    if not amount.is_finite():
        raise ValueError(f"invalid amount: {raw!r}")
    try:
        amount = amount.quantize(AMOUNT_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"amount out of range: {raw!r}")
    if negative:
        amount = -amount
    if abs(amount) > AMOUNT_MAX:
        raise ValueError(f"amount out of range: {raw!r}")
    return amount


def _sanitize_text(value: str, max_length: int) -> str:
    """Collapse whitespace and cap length so the value always fits the column."""
    return " ".join((value or "").split())[:max_length]


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


def _validate_header(header: list[str]) -> None:
    fields = [f.strip().lower() for f in header]
    expected = [h.lower() for h in REQUIRED_HEADERS]
    if fields != expected:
        raise CSVError(f"invalid header. Expected {REQUIRED_HEADERS}, got {header}")


def _parse_row(row: list[str]) -> dict:
    txn_date = _parse_date(row[0])
    description = _sanitize_text(row[1], DESCRIPTION_MAX)
    if not description:
        raise ValueError("missing description")
    amount = _parse_amount(row[2])
    ttype = _normalize_type(row[3])
    reference = _sanitize_text(row[4], REFERENCE_MAX) or None
    return {
        "date": txn_date,
        "description": description,
        "amount": amount,
        "type": ttype,
        "reference": reference,
    }


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
    _validate_header(header)

    rows: list[dict] = []
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        if not row or all((c or "").strip() == "" for c in row):
            continue  # skip blank lines
        if len(row) != len(REQUIRED_HEADERS):
            errors.append(f"row {i}: expected {len(REQUIRED_HEADERS)} columns, got {len(row)}")
            continue
        try:
            rows.append(_parse_row(row))
        except Exception as e:
            errors.append(f"row {i}: {e}")

    return rows, errors
