from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, Transaction, User
from app.schemas.insight import Insight


def _inr(value: Decimal) -> str:
    n = float(value)
    if abs(n) >= 1_00_00_000:
        return f"₹{n / 1_00_00_000:.1f}Cr"
    if abs(n) >= 1_00_000:
        return f"₹{n / 1_00_000:.1f}L"
    if abs(n) >= 1_000:
        return f"₹{n / 1_000:.1f}K"
    return f"₹{round(n)}"


def _sum(db: Session, user: User, ttype: str, start: date, end: date) -> Decimal:
    val = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == ttype,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .scalar()
    )
    return Decimal(val) if val is not None else Decimal("0")


def _by_category(db: Session, user: User, start: date, end: date) -> dict[int, Decimal]:
    rows = (
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == "DEBIT",
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Transaction.category_id)
        .all()
    )
    return {cid: Decimal(total) for cid, total in rows}


def build_insights(db: Session, user: User, date_from: date, date_to: date) -> list[Insight]:
    insights: list[Insight] = []
    length = (date_to - date_from).days + 1
    prev_end = date_from - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)

    cur_spend = _sum(db, user, "DEBIT", date_from, date_to)
    prev_spend = _sum(db, user, "DEBIT", prev_start, prev_end)
    income = _sum(db, user, "CREDIT", date_from, date_to)

    names = {
        c.id: c.name for c in db.query(Category).filter(Category.user_id == user.id).all()
    }

    # 1. Spending vs previous period
    if prev_spend > 0:
        pct = float((cur_spend - prev_spend) / prev_spend * 100)
        if pct <= -3:
            insights.append(
                Insight(
                    icon="trend-down",
                    tone="positive",
                    title=f"Spending down {abs(pct):.0f}%",
                    detail=f"You spent {_inr(cur_spend)} vs {_inr(prev_spend)} the period before.",
                )
            )
        elif pct >= 3:
            insights.append(
                Insight(
                    icon="trend-up",
                    tone="warning",
                    title=f"Spending up {pct:.0f}%",
                    detail=f"You spent {_inr(cur_spend)} vs {_inr(prev_spend)} the period before.",
                )
            )
        else:
            insights.append(
                Insight(
                    icon="trend-flat",
                    tone="neutral",
                    title="Spending is steady",
                    detail=f"About the same as the previous period ({_inr(cur_spend)}).",
                )
            )
    elif cur_spend > 0:
        insights.append(
            Insight(
                icon="trend-up",
                tone="info",
                title="First period of spending",
                detail=f"You spent {_inr(cur_spend)} with no earlier data to compare.",
            )
        )

    # 2. Savings rate
    if income > 0:
        net = income - cur_spend
        rate = float(net / income * 100)
        if rate >= 20:
            insights.append(
                Insight(
                    icon="piggy",
                    tone="positive",
                    title=f"You saved {rate:.0f}% of income",
                    detail=f"{_inr(net)} kept out of {_inr(income)} earned.",
                )
            )
        elif rate >= 0:
            insights.append(
                Insight(
                    icon="piggy",
                    tone="neutral",
                    title=f"Savings rate {rate:.0f}%",
                    detail=f"{_inr(net)} kept out of {_inr(income)} earned.",
                )
            )
        else:
            insights.append(
                Insight(
                    icon="piggy",
                    tone="warning",
                    title="Spending exceeds income",
                    detail=f"You spent {_inr(abs(net))} more than you earned this period.",
                )
            )

    # 3. Top category
    cats = _by_category(db, user, date_from, date_to)
    if cats and cur_spend > 0:
        top_id = max(cats, key=cats.get)
        share = float(cats[top_id] / cur_spend * 100)
        insights.append(
            Insight(
                icon="category",
                tone="info",
                title=f"{names.get(top_id, 'Other')} led your spending",
                detail=f"{_inr(cats[top_id])} · {share:.0f}% of the total.",
            )
        )

    # 4. Fastest-growing category
    prev_cats = _by_category(db, user, prev_start, prev_end)
    growth = []
    for cid, amount in cats.items():
        before = prev_cats.get(cid, Decimal("0"))
        if before >= 300:
            pct = float((amount - before) / before * 100)
            if pct >= 20:
                growth.append((pct, cid, amount, before))
    if growth:
        growth.sort(reverse=True)
        pct, cid, amount, before = growth[0]
        insights.append(
            Insight(
                icon="growth",
                tone="warning",
                title=f"{names.get(cid, 'A category')} rose {pct:.0f}%",
                detail=f"{_inr(before)} → {_inr(amount)} vs the previous period.",
            )
        )

    # 5. Most frequent merchant
    merchant = (
        db.query(
            Transaction.description,
            func.count(Transaction.id),
            func.sum(Transaction.amount),
        )
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == "DEBIT",
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Transaction.description)
        .order_by(func.count(Transaction.id).desc())
        .first()
    )
    if merchant and merchant[1] >= 2:
        insights.append(
            Insight(
                icon="store",
                tone="neutral",
                title=f"Most frequent: {merchant[0]}",
                detail=f"{merchant[1]} transactions totalling {_inr(Decimal(merchant[2]))}.",
            )
        )

    # 6. Largest single expense
    largest = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user.id,
            Transaction.type == "DEBIT",
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .order_by(Transaction.amount.desc())
        .first()
    )
    if largest:
        insights.append(
            Insight(
                icon="receipt",
                tone="neutral",
                title=f"Largest expense: {largest.description}",
                detail=f"{_inr(Decimal(largest.amount))} on {largest.date.strftime('%d %b %Y')}.",
            )
        )

    return insights[:6]
