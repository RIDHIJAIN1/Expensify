"""add validation check constraints

Revision ID: c0c83cea6095
Revises: 826398539364
Create Date: 2026-10-03 16:58:11.025329

Mirrors the application-layer validation at the database so bad data can
never be persisted even if a caller bypasses the API.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c0c83cea6095'
down_revision: Union[str, Sequence[str], None] = '826398539364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_categories_name_not_blank", "categories", "btrim(name) <> ''"
    )
    op.create_check_constraint(
        "ck_transactions_type_valid",
        "transactions",
        "type IN ('DEBIT', 'CREDIT')",
    )
    op.create_check_constraint(
        "ck_budgets_amount_positive", "budgets", "amount > 0"
    )
    op.create_check_constraint(
        "ck_uploads_status_valid",
        "uploads",
        "status IN ('PROCESSING', 'COMPLETED', 'FAILED')",
    )
    op.create_check_constraint(
        "ck_uploads_counts_non_negative",
        "uploads",
        "total_rows >= 0 AND imported_count >= 0 AND duplicate_count >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_uploads_counts_non_negative", "uploads", type_="check"
    )
    op.drop_constraint("ck_uploads_status_valid", "uploads", type_="check")
    op.drop_constraint("ck_budgets_amount_positive", "budgets", type_="check")
    op.drop_constraint(
        "ck_transactions_type_valid", "transactions", type_="check"
    )
    op.drop_constraint(
        "ck_categories_name_not_blank", "categories", type_="check"
    )
