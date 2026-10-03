from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import transaction
from app.models import Category, Transaction, User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.errors import ConflictError, NotFoundError, ValidationError


def _to_out(c: Category) -> CategoryOut:
    return CategoryOut(
        id=c.id,
        name=c.name,
        keywords=c.keywords.split(",") if c.keywords else [],
        is_custom=c.is_custom,
        color=c.color,
    )


def list_categories(db: Session, user: User) -> list[CategoryOut]:
    cats = (
        db.query(Category)
        .filter(Category.user_id == user.id)
        .order_by(Category.is_custom.asc(), Category.id.asc())
        .all()
    )
    return [_to_out(c) for c in cats]


def create_category(db: Session, user: User, body: CategoryCreate) -> CategoryOut:
    if db.query(Category).filter(Category.user_id == user.id, Category.name == body.name).first():
        raise ConflictError("Category already exists")
    cat = Category(
        user_id=user.id,
        name=body.name,
        keywords=",".join(body.keywords),
        is_custom=True,
        color=body.color,
    )
    try:
        with transaction(db):
            db.add(cat)
            db.flush()  # assign cat.id
    except IntegrityError:
        # A concurrent create won the race on uq_category_user_name.
        raise ConflictError("Category already exists")
    return _to_out(cat)


def update_category(
    db: Session, user: User, cat_id: int, body: CategoryUpdate
) -> CategoryOut:
    cat = db.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise NotFoundError("Category not found")
    try:
        with transaction(db):
            if body.name is not None:
                cat.name = body.name
            if body.keywords is not None:
                cat.keywords = ",".join(body.keywords)
            if body.color is not None:
                cat.color = body.color
    except IntegrityError:
        raise ConflictError("Category already exists")
    return _to_out(cat)


def delete_category(db: Session, user: User, cat_id: int) -> None:
    cat = db.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise NotFoundError("Category not found")
    if not cat.is_custom:
        raise ValidationError("Default categories cannot be deleted")
    with transaction(db):
        db.query(Transaction).filter(Transaction.category_id == cat.id).update(
            {Transaction.category_id: None}
        )
        db.delete(cat)
