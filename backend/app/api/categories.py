from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Category, Transaction, User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _to_out(c: Category) -> CategoryOut:
    return CategoryOut(
        id=c.id,
        name=c.name,
        keywords=c.keywords.split(",") if c.keywords else [],
        is_custom=c.is_custom,
        color=c.color,
    )


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    cats = (
        db.query(Category)
        .filter(Category.user_id == user.id)
        .order_by(Category.is_custom.asc(), Category.id.asc())
        .all()
    )
    return [_to_out(c) for c in cats]


@router.post("", status_code=201, response_model=CategoryOut)
def create_category(
    body: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    if db.query(Category).filter(Category.user_id == user.id, Category.name == body.name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = Category(
        user_id=user.id,
        name=body.name,
        keywords=",".join(body.keywords),
        is_custom=True,
        color=body.color,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return _to_out(cat)


@router.patch("/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    if body.name is not None:
        cat.name = body.name
    if body.keywords is not None:
        cat.keywords = ",".join(body.keywords)
    if body.color is not None:
        cat.color = body.color
    db.commit()
    db.refresh(cat)
    return _to_out(cat)


@router.delete("/{cat_id}")
def delete_category(
    cat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    cat = db.get(Category, cat_id)
    if not cat or cat.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    if not cat.is_custom:
        raise HTTPException(status_code=400, detail="Default categories cannot be deleted")
    db.query(Transaction).filter(Transaction.category_id == cat.id).update(
        {Transaction.category_id: None}
    )
    db.delete(cat)
    db.commit()
    return {"detail": "deleted"}
