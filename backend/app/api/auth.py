from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api import BAD_REQUEST, UNAUTHORIZED
from app.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, SignupRequest, UserOut
from app.schemas.common import MessageOut
from app.services import auth_service
from app.services.errors import AuthError

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={**BAD_REQUEST, **UNAUTHORIZED},
)

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
    user = auth_service.signup(db, body)
    _set_cookies(response, create_access_token(user), create_refresh_token(user))
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, body)
    _set_cookies(response, create_access_token(user), create_refresh_token(user))
    return UserOut.model_validate(user)


@router.post("/logout", response_model=MessageOut)
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")
    return MessageOut(detail="logged out")


@router.post("/refresh", response_model=MessageOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise AuthError("No refresh token")
    user = auth_service.user_from_refresh_token(db, token)
    access = create_access_token(user)
    response.set_cookie(
        "access_token", access, httponly=True, samesite="lax",
        secure=settings.COOKIE_SECURE, max_age=ACCESS_MAX_AGE, path="/",
    )
    return MessageOut(detail="refreshed")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
