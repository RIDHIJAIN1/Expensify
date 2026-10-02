import hashlib
from datetime import date
from decimal import Decimal


def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


def exact_fingerprint(
    txn_date: date, description: str, amount: Decimal, reference: str | None
) -> str:
    s = f"{txn_date}|{_norm(description)}|{amount}|{_norm(reference)}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def soft_fingerprint(txn_date: date, description: str, amount: Decimal) -> str:
    s = f"{txn_date}|{_norm(description)}|{amount}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
