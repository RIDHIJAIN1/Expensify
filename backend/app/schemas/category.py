from pydantic import BaseModel, Field, field_validator

HEX_COLOR_PATTERN = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
KEYWORD_MAX_LENGTH = 60
KEYWORDS_MAX_COUNT = 100


def _clean_name(value: object) -> object:
    if isinstance(value, str):
        name = " ".join(value.split())
        if not name:
            raise ValueError("name cannot be blank")
        return name
    return value


def _clean_keywords(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        keyword = " ".join((raw or "").split()).lower()
        if not keyword:
            continue
        if "," in keyword:
            raise ValueError("keywords cannot contain commas")
        if len(keyword) > KEYWORD_MAX_LENGTH:
            raise ValueError(f"keyword must be at most {KEYWORD_MAX_LENGTH} characters")
        if keyword in seen:
            continue
        seen.add(keyword)
        cleaned.append(keyword)
    if len(cleaned) > KEYWORDS_MAX_COUNT:
        raise ValueError(f"at most {KEYWORDS_MAX_COUNT} keywords are allowed")
    return cleaned


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    keywords: list[str] = Field(default_factory=list)
    color: str | None = Field(None, max_length=20, pattern=HEX_COLOR_PATTERN)

    _v_name = field_validator("name", mode="before")(_clean_name)
    _v_keywords = field_validator("keywords")(_clean_keywords)


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=60)
    keywords: list[str] | None = None
    color: str | None = Field(None, max_length=20, pattern=HEX_COLOR_PATTERN)

    _v_name = field_validator("name", mode="before")(_clean_name)
    _v_keywords = field_validator("keywords")(_clean_keywords)


class CategoryOut(BaseModel):
    id: int
    name: str
    keywords: list[str]
    is_custom: bool
    color: str | None

    model_config = {"from_attributes": True}
