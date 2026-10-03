"""add query indexes

Revision ID: 826398539364
Revises: 7461e5609f01
Create Date: 2026-10-03 16:53:04.731404

Replaces single-column indexes with composites that match the real access
paths (every query is scoped to a user), and adds the missing FK index on
transactions.upload_id. Purely indexes — no data or column changes.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '826398539364'
down_revision: Union[str, Sequence[str], None] = '7461e5609f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # categories: user_id list + per-user name lookups
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.create_index("ix_categories_user_name", "categories", ["user_id", "name"])

    # uploads: history ordered by created_at
    op.drop_index(op.f("ix_uploads_user_id"), table_name="uploads")
    op.create_index("ix_uploads_user_created_at", "uploads", ["user_id", "created_at"])

    # transactions: listing/export, aggregation, and dedupe access paths
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_soft_fingerprint"), table_name="transactions")
    op.create_index(
        "ix_transactions_user_date_id", "transactions", ["user_id", "date", "id"]
    )
    op.create_index(
        "ix_transactions_user_type_date", "transactions", ["user_id", "type", "date"]
    )
    op.create_index(
        "ix_transactions_user_soft_fingerprint",
        "transactions",
        ["user_id", "soft_fingerprint"],
    )
    op.create_index(
        op.f("ix_transactions_upload_id"), "transactions", ["upload_id"]
    )

    # budgets: user_id is the prefix of uq_budget_user_category, so the
    # dedicated index was redundant
    op.drop_index(op.f("ix_budgets_user_id"), table_name="budgets")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index(op.f("ix_budgets_user_id"), "budgets", ["user_id"])

    op.drop_index(op.f("ix_transactions_upload_id"), table_name="transactions")
    op.drop_index("ix_transactions_user_soft_fingerprint", table_name="transactions")
    op.drop_index("ix_transactions_user_type_date", table_name="transactions")
    op.drop_index("ix_transactions_user_date_id", table_name="transactions")
    op.create_index(
        op.f("ix_transactions_soft_fingerprint"), "transactions", ["soft_fingerprint"]
    )
    op.create_index(op.f("ix_transactions_date"), "transactions", ["date"])
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"])

    op.drop_index("ix_uploads_user_created_at", table_name="uploads")
    op.create_index(op.f("ix_uploads_user_id"), "uploads", ["user_id"])

    op.drop_index("ix_categories_user_name", table_name="categories")
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"])
