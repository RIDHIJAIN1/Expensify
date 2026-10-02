from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetSet(BaseModel):
    amount: Decimal = Field(gt=0)


class BudgetOut(BaseModel):
    category_id: int
    category_name: str
    color: str | None
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent: float
    over: bool
