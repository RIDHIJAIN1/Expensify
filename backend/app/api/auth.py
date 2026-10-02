from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    user_version,
    verify_password,
)
from app.database import get_db
from app.models import Category, User
from app.schemas.auth import LoginRequest, SignupRequest, UserOut
from app.services.classifier import DEFAULT_CATEGORIES

router = APIRouter(prefix="/api/auth", tags=["auth"])

ACCESS_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600


def _set_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        "access_token", access, httponly=True, samesite="lax",
        secure=settings.COOKIE_SECURE, max_age=ACCESS_MAX_AGE, path="/",
    )
    response.set_cookie(
        "refresh_token", refresh, httponly=True, samesite="lax",
        secure=settings.COOKIE_SECURE, max_age=REFRESH_MAX_AGE, path="/api/auth",
    )


@router.post("/signup", status_code=201, response_model=UserOut)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    db.add(user)
    db.flush()
    for c in DEFAULT_CATEGORIES:
        db.add(Category(
            user_id=user.id, name=c["name"],
            keywords=",".join(c["keywords"]), is_custom=False, color=c["color"],
        ))
    db.commit()
    _set_cookies(response, create_access_token(user), create_refresh_token(user))
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _set_cookies(response, create_access_token(user), create_refresh_token(user))
    return UserOut.model_validate(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")
    return {"detail": "logged out"}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user = db.get(User, int(payload.get("sub")))
    if not user or payload.get("uv") != user_version(user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    access = create_access_token(user)
    response.set_cookie(
        "access_token", access, httponly=True, samesite="lax",
        secure=settings.COOKIE_SECURE, max_age=ACCESS_MAX_AGE, path="/",
    )
    return {"detail": "refreshed"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
