from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.budget import BudgetOut, BudgetSet
from app.schemas.common import DateRangeQuery, MessageOut
from app.services import budget_service

router = APIRouter(
    prefix="/api/budgets",
    tags=["budgets"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    params: Annotated[DateRangeQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return budget_service.list_budgets(db, user, params.date_from, params.date_to)


@router.put("/{category_id}", response_model=BudgetOut)
def set_budget(
    category_id: int,
    body: BudgetSet,
    params: Annotated[DateRangeQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return budget_service.set_budget(
        db, user, category_id, body, params.date_from, params.date_to
    )


@router.delete("/{category_id}", response_model=MessageOut)
def delete_budget(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget_service.delete_budget(db, user, category_id)
    return MessageOut(detail="deleted")
