from datetime import datetime

from pydantic import BaseModel


class UploadOut(BaseModel):
    id: int
    filename: str
    status: str
    total_rows: int
    imported_count: int
    duplicate_count: int
    error_summary: list[str] | None
    created_at: datetime
