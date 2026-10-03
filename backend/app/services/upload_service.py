import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import transaction
from app.models import Category, Transaction, Upload, User
from app.schemas.upload import UploadOut
from app.services.classifier import classify_description
from app.services.csv_parser import CSVError, parse_csv
from app.services.dedupe import exact_fingerprint, soft_fingerprint
from app.services.errors import NotFoundError, ValidationError

_UPLOAD_LOCK_NAMESPACE = 42


def _to_out(u: Upload) -> UploadOut:
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


def _category_maps(db: Session, user_id: int) -> tuple[list[dict], dict[str, int]]:
    cats = (
        db.query(Category)
        .filter(Category.user_id == user_id)
        .order_by(Category.is_custom.asc(), Category.id.asc())
        .all()
    )
    cat_keywords = [
        {"name": c.name, "keywords": c.keywords.split(",") if c.keywords else []}
        for c in cats
    ]
    name_to_id = {c.name: c.id for c in cats}
    return cat_keywords, name_to_id


def _load_fingerprints(db: Session, user_id: int) -> tuple[set[str], set[str]]:
    exact = {
        f
        for (f,) in db.query(Transaction.fingerprint)
        .filter(Transaction.user_id == user_id)
        .all()
    }
    soft = {
        f
        for (f,) in db.query(Transaction.soft_fingerprint)
        .filter(Transaction.user_id == user_id)
        .all()
    }
    return exact, soft


def _fail(db: Session, upload: Upload, errors: list[str], total_rows: int | None = None) -> UploadOut:
    with transaction(db):
        upload.status = "FAILED"
        if total_rows is not None:
            upload.total_rows = total_rows
        upload.error_summary = json.dumps(errors[:20])
    return _to_out(upload)


def _category_id_for(
    row: dict, cat_keywords: list[dict], name_to_id: dict[str, int]
) -> int | None:
    # Credits are income by definition; only debits get keyword-classified.
    if row["type"] == "CREDIT":
        category_name = "Income"
    else:
        category_name = classify_description(row["description"], cat_keywords)
    return name_to_id.get(category_name)


def _is_duplicate(
    efp: str,
    sfp: str,
    existing_exact: set[str],
    existing_soft: set[str],
    seen_exact: set[str],
    seen_soft: set[str],
) -> bool:
    return efp in existing_exact or efp in seen_exact or sfp in existing_soft or sfp in seen_soft


def _new_transaction(
    row: dict, user_id: int, upload_id: int, category_id: int | None, efp: str, sfp: str
) -> Transaction:
    return Transaction(
        user_id=user_id,
        upload_id=upload_id,
        date=row["date"],
        description=row["description"],
        amount=row["amount"],
        type=row["type"],
        reference=row["reference"],
        category_id=category_id,
        fingerprint=efp,
        soft_fingerprint=sfp,
    )


def _insert_rows(
    db: Session,
    user: User,
    upload: Upload,
    rows: list[dict],
    cat_keywords: list[dict],
    name_to_id: dict[str, int],
    existing_exact: set[str],
    existing_soft: set[str],
) -> tuple[int, int]:
    seen_exact: set[str] = set()
    seen_soft: set[str] = set()
    imported = 0
    duplicates = 0
    batch: list[Transaction] = []

    for row in rows:
        efp = exact_fingerprint(row["date"], row["description"], row["amount"], row["reference"])
        sfp = soft_fingerprint(row["date"], row["description"], row["amount"])
        if _is_duplicate(efp, sfp, existing_exact, existing_soft, seen_exact, seen_soft):
            duplicates += 1
            continue

        category_id = _category_id_for(row, cat_keywords, name_to_id)
        batch.append(_new_transaction(row, user.id, upload.id, category_id, efp, sfp))
        seen_exact.add(efp)
        seen_soft.add(sfp)
        imported += 1

        if len(batch) >= 1000:  # batch flush for performance
            db.add_all(batch)
            db.flush()
            batch.clear()

    if batch:
        db.add_all(batch)
    return imported, duplicates


_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _sanitize_filename(filename: str) -> str:
    """Keep only the base name, drop control chars, and fit the column."""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = _CONTROL_CHARS.sub("", name).strip()
    return name[:255] or "upload.csv"


def process_upload(db: Session, user: User, filename: str, data: bytes) -> UploadOut:
    filename = _sanitize_filename(filename)
    upload = Upload(user_id=user.id, filename=filename, status="PROCESSING")
    db.add(upload)
    db.flush()  # assign upload.id

    try:
        rows, errors = parse_csv(data)
    except CSVError as e:
        return _fail(db, upload, [str(e)])

    total_rows = len(rows) + len(errors)
    if total_rows > settings.MAX_UPLOAD_ROWS:
        raise ValidationError(
            f"File has too many rows ({total_rows}). Max {settings.MAX_UPLOAD_ROWS}"
        )

    if not rows and errors:
        # nothing parseable at all
        return _fail(db, upload, errors, total_rows=total_rows)

    with transaction(db):
        # Serialize uploads per user so concurrent files cannot race the
        # dedupe check or trip the unique fingerprint constraint.
        db.execute(
            text("SELECT pg_advisory_xact_lock(:ns, :uid)"),
            {"ns": _UPLOAD_LOCK_NAMESPACE, "uid": user.id},
        )
        cat_keywords, name_to_id = _category_maps(db, user.id)
        existing_exact, existing_soft = _load_fingerprints(db, user.id)

        imported, duplicates = _insert_rows(
            db, user, upload, rows, cat_keywords, name_to_id, existing_exact, existing_soft
        )
        upload.status = "COMPLETED"
        upload.total_rows = total_rows
        upload.imported_count = imported
        upload.duplicate_count = duplicates
        upload.error_summary = json.dumps(errors[:20]) if errors else None

    return _to_out(upload)


def list_uploads(db: Session, user: User) -> list[UploadOut]:
    uploads = (
        db.query(Upload)
        .filter(Upload.user_id == user.id)
        .order_by(Upload.created_at.desc())
        .all()
    )
    return [_to_out(u) for u in uploads]


def get_upload(db: Session, user: User, upload_id: int) -> UploadOut:
    upload = db.get(Upload, upload_id)
    if not upload or upload.user_id != user.id:
        raise NotFoundError("Upload not found")
    return _to_out(upload)
