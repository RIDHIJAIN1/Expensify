from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetSet(BaseModel):
    # Bounds match the numeric(12, 2) DB column exactly.
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetOut(BaseModel):
    category_id: int
    category_name: str
    color: str | None
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent: float
    over: bool
