from datetime import date

from pydantic import BaseModel


class MessageOut(BaseModel):
    detail: str


class ErrorOut(BaseModel):
    detail: str


class HealthOut(BaseModel):
    status: str


class DateRangeQuery(BaseModel):
    date_from: date | None = None
    date_to: date | None = None


class RequiredDateRangeQuery(BaseModel):
    date_from: date
    date_to: date


class TransactionFilterQuery(DateRangeQuery):
    category_id: int | None = None
    type: str | None = None
