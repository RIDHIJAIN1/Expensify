from datetime import date

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import transaction
from app.models import Category, Transaction, User
from app.schemas.transaction import (
    TransactionOut,
    TransactionUpdate,
    TransactionUpdateResult,
)
from app.services.classifier import learned_keyword
from app.services.errors import NotFoundError, ValidationError


def _to_out(t: Transaction) -> TransactionOut:
    return TransactionOut(
        id=t.id,
        date=t.date,
        description=t.description,
        amount=t.amount,
        type=t.type,
        reference=t.reference,
        category_id=t.category_id,
        category_name=t.category.name if t.category else None,
    )


def _apply_filters(
    q,
    date_from: date | None,
    date_to: date | None,
    category_id: int | None,
    type: str | None,
    search: str | None,
):
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    if category_id is not None:
        q = q.filter(Transaction.category_id == category_id)
    if type:
        q = q.filter(Transaction.type == type.upper())
    if search:
        q = q.filter(Transaction.description.ilike(f"%{search}%"))
    return q


def list_transactions(
    db: Session,
    user: User,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    type: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    q = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user.id)
    )
    q = _apply_filters(q, date_from, date_to, category_id, type, search)

    total = q.count()
    rows = (
        q.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": [_to_out(t) for t in rows]}


def get_transaction(db: Session, user: User, tx_id: int) -> TransactionOut:
    t = db.get(Transaction, tx_id)
    if not t or t.user_id != user.id:
        raise NotFoundError("Transaction not found")
    return _to_out(t)


def _append_keyword(cat: Category, candidate: str) -> bool:
    if not candidate or "," in candidate or len(candidate) > 60:
        return False
    existing = {
        k.strip().lower() for k in (cat.keywords or "").split(",") if k.strip()
    }
    if candidate in existing:
        return False
    cat.keywords = f"{cat.keywords},{candidate}" if cat.keywords else candidate
    return True


def _remove_keyword_from_others(
    db: Session, user: User, keep_cat_id: int, candidate: str
) -> None:
    """Drop the keyword from other categories so the latest intent wins."""
    others = (
        db.query(Category)
        .filter(Category.user_id == user.id, Category.id != keep_cat_id)
        .all()
    )
    for other in others:
        current = [
            k.strip() for k in (other.keywords or "").split(",") if k.strip()
        ]
        kept = [k for k in current if k.lower() != candidate]
        if len(kept) != len(current):
            other.keywords = ",".join(kept)


def _reclassify_matches(
    db: Session, user: User, tx_id: int, description: str, cat_id: int
) -> int:
    """Apply a learned rule to matching not-yet-classified rows.

    Matches either truly uncategorized transactions or ones sitting in the
    "Other" fallback category.
    """
    normalized = " ".join(description.lower().split())
    other = (
        db.query(Category)
        .filter(Category.user_id == user.id, Category.name == "Other")
        .first()
    )
    unclassified = [Transaction.category_id.is_(None)]
    if other:
        unclassified.append(Transaction.category_id == other.id)
    return (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user.id,
            Transaction.id != tx_id,
            or_(*unclassified),
            func.lower(Transaction.description) == normalized,
        )
        .update({Transaction.category_id: cat_id}, synchronize_session=False)
    )


def _learn_from_recategorization(
    db: Session, user: User, t: Transaction, cat: Category
) -> tuple[str | None, int]:
    candidate = learned_keyword(t.description)
    if not candidate or not _append_keyword(cat, candidate):
        return None, 0
    _remove_keyword_from_others(db, user, cat.id, candidate)
    reclassified = _reclassify_matches(db, user, t.id, t.description, cat.id)
    return candidate, reclassified


def update_transaction(
    db: Session, user: User, tx_id: int, body: TransactionUpdate
) -> TransactionUpdateResult:
    t = db.get(Transaction, tx_id)
    if not t or t.user_id != user.id:
        raise NotFoundError("Transaction not found")

    learned: str | None = None
    reclassified = 0

    with transaction(db):
        if body.category_id is not None:
            cat = db.get(Category, body.category_id)
            if not cat or cat.user_id != user.id:
                raise ValidationError("Invalid category")
            if t.category_id != cat.id:
                learned, reclassified = _learn_from_recategorization(db, user, t, cat)

        t.category_id = body.category_id

    db.refresh(t)
    return TransactionUpdateResult(
        transaction=_to_out(t), learned_keyword=learned, reclassified=reclassified
    )
