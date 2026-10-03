from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.common import RequiredDateRangeQuery
from app.schemas.insight import Insight
from app.services.insights import build_insights

router = APIRouter(
    prefix="/api/insights",
    tags=["insights"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=list[Insight])
def get_insights(
    params: Annotated[RequiredDateRangeQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return build_insights(db, user, params.date_from, params.date_to)
