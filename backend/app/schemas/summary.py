from decimal import Decimal

from pydantic import BaseModel


class CategoryTotal(BaseModel):
    category_id: int | None
    category_name: str
    total: Decimal
    count: int


class MonthlyTotal(BaseModel):
    month: str  # "YYYY-MM"
    debit: Decimal
    credit: Decimal
    count: int


class MerchantTotal(BaseModel):
    name: str
    total: Decimal
    count: int


class SummaryOut(BaseModel):
    total_income: Decimal
    total_spent: Decimal
    net: Decimal
    transaction_count: int
    by_category: list[CategoryTotal]
    by_month: list[MonthlyTotal]
    top_merchants: list[MerchantTotal]
