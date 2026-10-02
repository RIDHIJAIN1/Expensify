from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, literal_column
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas.summary import CategoryTotal, MerchantTotal, MonthlyTotal, SummaryOut

router = APIRouter(prefix="/api/summary", tags=["summary"])


def _filtered(db: Session, user: User, date_from: date | None, date_to: date | None):
    q = db.query(Transaction).filter(Transaction.user_id == user.id)
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    return q


@router.get("", response_model=SummaryOut)
def get_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
):
    base = _filtered(db, user, date_from, date_to)

    def _sum(ttype: str) -> Decimal:
        val = (
            base.filter(Transaction.type == ttype)
            .with_entities(func.coalesce(func.sum(Transaction.amount), 0))
            .scalar()
        )
        return Decimal(val) if val is not None else Decimal("0")

    total_income = _sum("CREDIT")
    total_spent = _sum("DEBIT")
    net = total_income - total_spent
    transaction_count = base.count()

    # Spending by category (DEBIT only)
    cat_rows = (
        base.filter(Transaction.type == "DEBIT")
        .with_entities(
            Transaction.category_id,
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        )
        .group_by(Transaction.category_id)
        .all()
    )
    cat_names = {
        c.id: c.name for c in db.query(Category).filter(Category.user_id == user.id).all()
    }
    by_category = [
        CategoryTotal(
            category_id=cid,
            category_name=cat_names.get(cid, "Uncategorized"),
            total=Decimal(total),
            count=count,
        )
        for cid, total, count in cat_rows
    ]

    # Monthly debit + credit
    month_expr = func.date_trunc(literal_column("'month'"), Transaction.date)
    month_rows = (
        base.with_entities(month_expr, Transaction.type, func.sum(Transaction.amount))
        .group_by(month_expr, Transaction.type)
        .order_by(month_expr)
        .all()
    )
    months: dict[str, dict[str, Decimal]] = {}
    for m, ttype, total in month_rows:
        key = m.strftime("%Y-%m")
        bucket = months.setdefault(key, {"debit": Decimal("0"), "credit": Decimal("0")})
        bucket["debit" if ttype == "DEBIT" else "credit"] = Decimal(total)

    count_rows = (
        base.with_entities(month_expr, func.count(Transaction.id))
        .group_by(month_expr)
        .all()
    )
    counts = {m.strftime("%Y-%m"): c for m, c in count_rows}
    by_month = [
        MonthlyTotal(
            month=k,
            debit=v["debit"],
            credit=v["credit"],
            count=counts.get(k, 0),
        )
        for k, v in months.items()
    ]

    # Top merchants (DEBIT only)
    merchant_rows = (
        base.filter(Transaction.type == "DEBIT")
        .with_entities(
            Transaction.description,
            func.sum(Transaction.amount),
            func.count(Transaction.id),
        )
        .group_by(Transaction.description)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )
    top_merchants = [
        MerchantTotal(name=name, total=Decimal(total), count=count)
        for name, total, count in merchant_rows
    ]

    return SummaryOut(
        total_income=total_income,
        total_spent=total_spent,
        net=net,
        transaction_count=transaction_count,
        by_category=by_category,
        by_month=by_month,
        top_merchants=top_merchants,
    )
