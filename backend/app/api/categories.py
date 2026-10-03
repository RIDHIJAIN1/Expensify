from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import COMMON_ERROR_RESPONSES
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import MessageOut
from app.services import category_service

router = APIRouter(
    prefix="/api/categories",
    tags=["categories"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return category_service.list_categories(db, user)


@router.post("", status_code=201, response_model=CategoryOut)
def create_category(
    body: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return category_service.create_category(db, user, body)


@router.patch("/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return category_service.update_category(db, user, cat_id, body)


@router.delete("/{cat_id}", response_model=MessageOut)
def delete_category(
    cat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    category_service.delete_category(db, user, cat_id)
    return MessageOut(detail="deleted")
