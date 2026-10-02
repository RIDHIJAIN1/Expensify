from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint", name="uq_user_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    upload_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # DEBIT / CREDIT
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)  # exact dedupe
    soft_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # overlap dedupe
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user = relationship("User", back_populates="transactions")
    upload = relationship("Upload", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
