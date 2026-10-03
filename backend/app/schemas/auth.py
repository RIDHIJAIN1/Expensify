from pydantic import BaseModel, EmailStr, Field, field_validator

# bcrypt 5 rejects inputs longer than 72 *bytes* (not characters).
PASSWORD_MAX_BYTES = 72


def _normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(f"password must be at most {PASSWORD_MAX_BYTES} bytes")
    return value


def _clean_name(value: object) -> object:
    if isinstance(value, str):
        name = " ".join(value.split())
        return name or None
    return value


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=PASSWORD_MAX_BYTES)
    name: str | None = Field(None, max_length=120)

    _v_email = field_validator("email", mode="before")(_normalize_email)
    _v_password = field_validator("password")(_check_password_bytes)
    _v_name = field_validator("name", mode="before")(_clean_name)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_BYTES)

    _v_email = field_validator("email", mode="before")(_normalize_email)
    _v_password = field_validator("password")(_check_password_bytes)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None

    model_config = {"from_attributes": True}
