from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = (
        # Upload history: WHERE user_id ORDER BY created_at DESC
        Index("ix_uploads_user_created_at", "user_id", "created_at"),
        CheckConstraint(
            "status IN ('PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_uploads_status_valid",
        ),
        CheckConstraint(
            "total_rows >= 0 AND imported_count >= 0 AND duplicate_count >= 0",
            name="ck_uploads_counts_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PROCESSING")  # PROCESSING/COMPLETED/FAILED
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user = relationship("User", back_populates="uploads")
    transactions = relationship("Transaction", back_populates="upload")
