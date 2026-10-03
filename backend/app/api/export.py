from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.common import DateRangeQuery, TransactionFilterQuery
from app.services import export_service

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get(
    "/csv",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/csv": {}}, "description": "CSV export"}},
)
def export_csv(
    params: Annotated[TransactionFilterQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = export_service.build_csv(
        db, user,
        date_from=params.date_from, date_to=params.date_to,
        category_id=params.category_id, type_=params.type,
    )
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get(
    "/pdf",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF report"}},
)
def export_pdf(
    params: Annotated[DateRangeQuery, Query()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = export_service.build_pdf(
        db, user, date_from=params.date_from, date_to=params.date_to
    )
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"},
    )
