from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas.transaction import (
    TransactionOut,
    TransactionUpdate,
    TransactionUpdateResult,
)
from app.services.classifier import learned_keyword

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


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


@router.get("")
def list_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    type: str | None = None,
    search: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == user.id)
    )
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

    total = q.count()
    rows = (
        q.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": [_to_out(t) for t in rows]}


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    t = db.get(Transaction, tx_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return _to_out(t)


@router.patch("/{tx_id}", response_model=TransactionUpdateResult)
def update_transaction(
    tx_id: int,
    body: TransactionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.get(Transaction, tx_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")

    learned: str | None = None
    reclassified = 0

    if body.category_id is not None:
        cat = db.get(Category, body.category_id)
        if not cat or cat.user_id != user.id:
            raise HTTPException(status_code=400, detail="Invalid category")

        if t.category_id != cat.id:
            candidate = learned_keyword(t.description)
            if candidate:
                existing = {
                    k.strip().lower()
                    for k in (cat.keywords or "").split(",")
                    if k.strip()
                }
                if candidate not in existing:
                    cat.keywords = f"{cat.keywords},{candidate}" if cat.keywords else candidate
                    learned = candidate

                    # Drop the keyword from other categories so the latest intent wins.
                    others = (
                        db.query(Category)
                        .filter(Category.user_id == user.id, Category.id != cat.id)
                        .all()
                    )
                    for other in others:
                        current = [
                            k.strip()
                            for k in (other.keywords or "").split(",")
                            if k.strip()
                        ]
                        kept = [k for k in current if k.lower() != candidate]
                        if len(kept) != len(current):
                            other.keywords = ",".join(kept)

                    # Apply the learned rule to matching not-yet-classified rows
                    # (either truly uncategorized or sitting in the "Other" fallback).
                    normalized = " ".join(t.description.lower().split())
                    other = (
                        db.query(Category)
                        .filter(Category.user_id == user.id, Category.name == "Other")
                        .first()
                    )
                    unclassified = [Transaction.category_id.is_(None)]
                    if other:
                        unclassified.append(Transaction.category_id == other.id)
                    reclassified = (
                        db.query(Transaction)
                        .filter(
                            Transaction.user_id == user.id,
                            Transaction.id != t.id,
                            or_(*unclassified),
                            func.lower(Transaction.description) == normalized,
                        )
                        .update(
                            {Transaction.category_id: cat.id}, synchronize_session=False
                        )
                    )

    t.category_id = body.category_id
    db.commit()
    db.refresh(t)
    return TransactionUpdateResult(
        transaction=_to_out(t), learned_keyword=learned, reclassified=reclassified
    )
