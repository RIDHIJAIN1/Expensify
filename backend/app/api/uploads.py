from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api import COMMON_ERROR_RESPONSES
from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.upload import UploadOut
from app.services import upload_service

router = APIRouter(
    prefix="/api/uploads",
    tags=["uploads"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.post("", status_code=201, response_model=UploadOut)
async def create_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Extension check
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    data = await file.read()

    # Size cap
    if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)"
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # MIME sniffing: binaries contain NUL bytes in the first chunk
    if b"\x00" in data[:1024]:
        raise HTTPException(status_code=400, detail="File is not a valid CSV (binary content detected)")

    # Parsing/classification/insertion is CPU + DB heavy: keep it off the
    # event loop so health checks and reads stay responsive during uploads.
    return await run_in_threadpool(
        upload_service.process_upload, db, user, file.filename, data
    )


@router.get("", response_model=list[UploadOut])
def list_uploads(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return upload_service.list_uploads(db, user)


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(
    upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return upload_service.get_upload(db, user, upload_id)
