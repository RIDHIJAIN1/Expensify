from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database import transaction
from app.models import Budget, Category, Transaction, User
from app.schemas.budget import BudgetOut, BudgetSet
from app.services.errors import NotFoundError


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


def list_budgets(
    db: Session, user: User, date_from: date | None, date_to: date | None
) -> list[BudgetOut]:
    spent = _spent_map(db, user, date_from, date_to)
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    out = [_to_out(b, spent.get(b.category_id, Decimal("0"))) for b in budgets]
    out.sort(key=lambda x: -x.percent)
    return out


def set_budget(
    db: Session,
    user: User,
    category_id: int,
    body: BudgetSet,
    date_from: date | None = None,
    date_to: date | None = None,
) -> BudgetOut:
    cat = db.get(Category, category_id)
    if not cat or cat.user_id != user.id:
        raise NotFoundError("Category not found")
    # Atomic upsert: concurrent puts for the same category cannot race the
    # unique (user_id, category_id) index.
    with transaction(db):
        db.execute(
            pg_insert(Budget.__table__)
            .values(user_id=user.id, category_id=category_id, amount=body.amount)
            .on_conflict_do_update(
                constraint="uq_budget_user_category",
                set_={"amount": body.amount},
            )
        )
    budget = (
        db.query(Budget)
        .filter(Budget.user_id == user.id, Budget.category_id == category_id)
        .one()
    )
    spent = _spent_map(db, user, date_from, date_to).get(category_id, Decimal("0"))
    return _to_out(budget, spent)


def delete_budget(db: Session, user: User, category_id: int) -> None:
    budget = (
        db.query(Budget)
        .filter(Budget.user_id == user.id, Budget.category_id == category_id)
        .first()
    )
    if not budget:
        raise NotFoundError("Budget not found")
    with transaction(db):
        db.delete(budget)
