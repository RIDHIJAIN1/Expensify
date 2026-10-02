import json

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Category, Transaction, Upload, User
from app.services.classifier import classify_description
from app.services.csv_parser import CSVError, parse_csv
from app.services.dedupe import exact_fingerprint, soft_fingerprint


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


def process_upload(db: Session, user: User, filename: str, data: bytes) -> Upload:
    upload = Upload(user_id=user.id, filename=filename, status="PROCESSING")
    db.add(upload)
    db.flush()  # assign upload.id

    try:
        rows, errors = parse_csv(data)
    except CSVError as e:
        upload.status = "FAILED"
        upload.error_summary = json.dumps([str(e)])
        db.commit()
        return upload

    if not rows and errors:
        # nothing parseable at all
        upload.status = "FAILED"
        upload.total_rows = len(errors)
        upload.error_summary = json.dumps(errors[:20])
        db.commit()
        return upload

    cat_keywords, name_to_id = _category_maps(db, user.id)

    # Existing fingerprints for cross-upload dedupe
    existing_exact = {
        f for (f,) in db.query(Transaction.fingerprint).filter(Transaction.user_id == user.id).all()
    }
    existing_soft = {
        f for (f,) in db.query(Transaction.soft_fingerprint).filter(Transaction.user_id == user.id).all()
    }
    seen_exact: set[str] = set()
    seen_soft: set[str] = set()

    imported = 0
    duplicates = 0
    to_insert: list[Transaction] = []

    for row in rows:
        efp = exact_fingerprint(row["date"], row["description"], row["amount"], row["reference"])
        sfp = soft_fingerprint(row["date"], row["description"], row["amount"])

        if efp in existing_exact or efp in seen_exact:
            duplicates += 1
            continue
        if sfp in existing_soft or sfp in seen_soft:
            duplicates += 1  # overlapping / likely duplicate
            continue

        # Credits are income by definition; only debits get keyword-classified.
        if row["type"] == "CREDIT":
            category_name = "Income"
        else:
            category_name = classify_description(row["description"], cat_keywords)
        category_id = name_to_id.get(category_name)

        to_insert.append(
            Transaction(
                user_id=user.id,
                upload_id=upload.id,
                date=row["date"],
                description=row["description"],
                amount=row["amount"],
                type=row["type"],
                reference=row["reference"],
                category_id=category_id,
                fingerprint=efp,
                soft_fingerprint=sfp,
            )
        )
        seen_exact.add(efp)
        seen_soft.add(sfp)
        imported += 1

        if len(to_insert) >= 1000:  # batch flush for performance
            db.add_all(to_insert)
            db.flush()
            to_insert.clear()

    if to_insert:
        db.add_all(to_insert)

    upload.status = "COMPLETED"
    upload.total_rows = len(rows) + len(errors)
    upload.imported_count = imported
    upload.duplicate_count = duplicates
    upload.error_summary = json.dumps(errors[:20]) if errors else None
    db.commit()
    return upload
