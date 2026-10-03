from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.transaction import (
    TransactionListOut,
    TransactionOut,
    TransactionQuery,
    TransactionUpdate,
    TransactionUpdateResult,
)
from app.services import transaction_service

router = APIRouter(
    prefix="/api/transactions",
    tags=["transactions"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=TransactionListOut)
def list_transactions(
    filters: Annotated[TransactionQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return transaction_service.list_transactions(
        db, user,
        date_from=filters.date_from, date_to=filters.date_to,
        category_id=filters.category_id, type=filters.type,
        search=filters.search, limit=filters.limit, offset=filters.offset,
    )


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return transaction_service.get_transaction(db, user, tx_id)


@router.patch("/{tx_id}", response_model=TransactionUpdateResult)
def update_transaction(
    tx_id: int,
    body: TransactionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return transaction_service.update_transaction(db, user, tx_id, body)
