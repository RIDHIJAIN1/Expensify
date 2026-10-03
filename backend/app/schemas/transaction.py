from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import TransactionFilterQuery


class TransactionOut(BaseModel):
    id: int
    date: date
    description: str
    amount: Decimal
    type: str
    reference: str | None
    category_id: int | None
    category_name: str | None = None


class TransactionQuery(TransactionFilterQuery):
    search: str | None = Field(None, max_length=200)
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class TransactionListOut(BaseModel):
    total: int
    items: list[TransactionOut]


class TransactionUpdate(BaseModel):
    category_id: int | None = Field(None, gt=0)


class TransactionUpdateResult(BaseModel):
    transaction: TransactionOut
    learned_keyword: str | None = None
    reclassified: int = 0
