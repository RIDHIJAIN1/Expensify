"""enforce unique category names

Revision ID: 6cfdceb57cd8
Revises: c0c83cea6095
Create Date: 2026-10-03 17:12:31.367053

Category names must be unique per user. Existing duplicates (created by the
old check-then-insert race) are merged into the earliest row: transactions are
re-pointed, budgets are moved where possible, then the duplicate rows are
deleted.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6cfdceb57cd8'
down_revision: Union[str, Sequence[str], None] = 'c0c83cea6095'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DUPES = """
    SELECT id, user_id, name, min(id) OVER (PARTITION BY user_id, name) AS keep_id
    FROM categories
"""


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Re-point transactions from duplicate categories to the kept row.
    op.execute(
        f"""
        UPDATE transactions t
        SET category_id = d.keep_id
        FROM ({_DUPES}) d
        WHERE t.category_id = d.id AND d.id <> d.keep_id
        """
    )

    # 2. Move budgets to the kept row where it has no budget yet...
    op.execute(
        f"""
        UPDATE budgets b
        SET category_id = d.keep_id
        FROM ({_DUPES}) d
        WHERE b.category_id = d.id AND d.id <> d.keep_id
          AND NOT EXISTS (
              SELECT 1 FROM budgets kb
              WHERE kb.user_id = b.user_id AND kb.category_id = d.keep_id
          )
        """
    )
    # ...and drop budgets that would collide with an existing kept budget.
    op.execute(
        f"""
        DELETE FROM budgets b
        USING ({_DUPES}) d
        WHERE b.category_id = d.id AND d.id <> d.keep_id
        """
    )

    # 3. Remove the duplicate categories, then enforce uniqueness.
    op.execute(
        f"""
        DELETE FROM categories c
        USING ({_DUPES}) d
        WHERE c.id = d.id AND d.id <> d.keep_id
        """
    )
    op.drop_index("ix_categories_user_name", table_name="categories")
    op.create_unique_constraint(
        "uq_category_user_name", "categories", ["user_id", "name"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_category_user_name", "categories", type_="unique")
    op.create_index(
        "ix_categories_user_name", "categories", ["user_id", "name"]
    )
