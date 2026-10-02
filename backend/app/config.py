import ssl
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    DATABASE_URL: str = "postgresql+pg8000://expense:expense@localhost:55432/expense"

    # Auth
    JWT_SECRET: str = "change-me-in-production-please-use-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload limits
    MAX_UPLOAD_MB: int = 10
    MAX_UPLOAD_ROWS: int = 50000

    # CORS (comma-separated origins, for local dev only)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    COOKIE_SECURE: bool = False

    # Static frontend directory (served by FastAPI in production)
    STATIC_DIR: str = "static"


settings = Settings()

# Query-string params added by managed providers that pg8000 does not accept.
_UNSUPPORTED_PARAMS = {"sslmode", "channel_binding"}


def get_database_url() -> str:
    """Return a SQLAlchemy/pg8000-ready URL.

    Normalizes PaaS schemes (`postgres://`, `postgresql://` → `postgresql+pg8000://`)
    and drops SSL params the driver doesn't understand (we enable TLS ourselves).
    """
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+pg8000://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+pg8000://", 1)

    parts = urlsplit(url)
    if parts.query:
        keep = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_PARAMS]
        url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(keep), parts.fragment)
        )
    return url


def get_connect_args() -> dict:
    """Managed Postgres (Neon/Render/Supabase) requires TLS; local dev does not."""
    host = urlsplit(get_database_url()).hostname
    if host in (None, "", "localhost", "127.0.0.1", "db"):
        return {}
    return {"ssl_context": ssl.create_default_context()}
