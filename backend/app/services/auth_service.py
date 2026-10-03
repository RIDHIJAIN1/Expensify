from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import decode_token, hash_password, user_version, verify_password
from app.database import transaction
from app.models import Category, User
from app.schemas.auth import LoginRequest, SignupRequest
from app.services.classifier import DEFAULT_CATEGORIES
from app.services.errors import AuthError, ConflictError


def signup(db: Session, body: SignupRequest) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise ConflictError("Email already registered")
    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    try:
        with transaction(db):
            db.add(user)
            db.flush()  # assign user.id
            for c in DEFAULT_CATEGORIES:
                db.add(Category(
                    user_id=user.id, name=c["name"],
                    keywords=",".join(c["keywords"]), is_custom=False, color=c["color"],
                ))
    except IntegrityError:
        # A concurrent signup won the race on the unique email index.
        raise ConflictError("Email already registered")
    return user


def authenticate(db: Session, body: LoginRequest) -> User:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise AuthError("Invalid email or password")
    return user


def user_from_refresh_token(db: Session, token: str) -> User:
    try:
        payload = decode_token(token)
    except Exception:
        raise AuthError("Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise AuthError("Invalid token type")
    user = db.get(User, int(payload.get("sub")))
    if not user or payload.get("uv") != user_version(user.password_hash):
        raise AuthError("Invalid or expired refresh token")
    return user
