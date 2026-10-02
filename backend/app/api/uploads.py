import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import Upload, User
from app.schemas.upload import UploadOut
from app.services.upload_service import process_upload

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def _upload_out(u: Upload) -> UploadOut:
    return UploadOut(
        id=u.id,
        filename=u.filename,
        status=u.status,
        total_rows=u.total_rows,
        imported_count=u.imported_count,
        duplicate_count=u.duplicate_count,
        error_summary=json.loads(u.error_summary) if u.error_summary else None,
        created_at=u.created_at,
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

    upload = process_upload(db, user, file.filename, data)
    return _upload_out(upload)


@router.get("", response_model=list[UploadOut])
def list_uploads(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    uploads = (
        db.query(Upload)
        .filter(Upload.user_id == user.id)
        .order_by(Upload.created_at.desc())
        .all()
    )
    return [_upload_out(u) for u in uploads]


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(
    upload_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    u = db.get(Upload, upload_id)
    if not u or u.user_id != user.id:
        raise HTTPException(status_code=404, detail="Upload not found")
    return _upload_out(u)
