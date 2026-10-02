from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Budget, Category, Transaction, User
from app.schemas.budget import BudgetOut, BudgetSet

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


def _spent_map(
    db: Session, user: User, date_from: date | None, date_to: date | None
) -> dict[int, Decimal]:
    q = db.query(Transaction.category_id, func.sum(Transaction.amount)).filter(
        Transaction.user_id == user.id, Transaction.type == "DEBIT"
    )
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    return {cid: Decimal(total) for cid, total in q.group_by(Transaction.category_id).all()}


def _to_out(budget: Budget, spent: Decimal) -> BudgetOut:
    limit = Decimal(budget.amount)
    remaining = limit - spent
    percent = float(spent / limit * 100) if limit > 0 else 0.0
    return BudgetOut(
        category_id=budget.category_id,
        category_name=budget.category.name,
        color=budget.category.color,
        limit=limit,
        spent=spent,
        remaining=remaining,
        percent=round(percent, 1),
        over=spent > limit,
    )


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    spent = _spent_map(db, user, date_from, date_to)
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    out = [_to_out(b, spent.get(b.category_id, Decimal("0"))) for b in budgets]
    out.sort(key=lambda x: -x.percent)
    return out


@router.put("/{category_id}", response_model=BudgetOut)
def set_budget(
    category_id: int,
    body: BudgetSet,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.get(Category, category_id)
    if not cat or cat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    budget = (
        db.query(Budget)
        .filter(Budget.user_id == user.id, Budget.category_id == category_id)
        .first()
    )
    if budget is None:
        budget = Budget(user_id=user.id, category_id=category_id, amount=body.amount)
        db.add(budget)
    else:
        budget.amount = body.amount
    db.commit()
    db.refresh(budget)
    spent = _spent_map(db, user, date_from, date_to).get(category_id, Decimal("0"))
    return _to_out(budget, spent)


@router.delete("/{category_id}")
def delete_budget(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    budget = (
        db.query(Budget)
        .filter(Budget.user_id == user.id, Budget.category_id == category_id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return {"detail": "deleted"}
