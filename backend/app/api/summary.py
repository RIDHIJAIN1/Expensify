from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.common import DateRangeQuery
from app.schemas.summary import SummaryOut
from app.services import summary_service

router = APIRouter(
    prefix="/api/summary",
    tags=["summary"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=SummaryOut)
def get_summary(
    params: Annotated[DateRangeQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return summary_service.build_summary(db, user, params.date_from, params.date_to)
