from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TransactionOut(BaseModel):
    id: int
    date: date
    description: str
    amount: Decimal
    type: str
    reference: str | None
    category_id: int | None
    category_name: str | None = None


class TransactionUpdate(BaseModel):
    category_id: int | None = None


class TransactionUpdateResult(BaseModel):
    transaction: TransactionOut
    learned_keyword: str | None = None
    reclassified: int = 0
