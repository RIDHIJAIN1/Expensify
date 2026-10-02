import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def user_version(password_hash: str) -> str:
    """Short fingerprint bound to a user's credentials.

    Included in tokens so that a token issued for one account can never be
    accepted for another (e.g. after a database reset re-uses ids), and so
    that changing a password invalidates existing sessions.
    """
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def _create_token(subject: str, token_type: str, expires_delta: timedelta, uv: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "uv": uv,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user) -> str:
    return _create_token(
        str(user.id), "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        user_version(user.password_hash),
    )


def create_refresh_token(user) -> str:
    return _create_token(
        str(user.id), "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_version(user.password_hash),
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
