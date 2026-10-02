from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    keywords: list[str] = []
    color: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
    color: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    keywords: list[str]
    is_custom: bool
    color: str | None

    model_config = {"from_attributes": True}
