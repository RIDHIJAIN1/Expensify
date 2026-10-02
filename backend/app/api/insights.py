from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.insight import Insight
from app.services.insights import build_insights

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=list[Insight])
def get_insights(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return build_insights(db, user, date_from, date_to)
