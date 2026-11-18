"""add_category_to_dishes

Revision ID: 18d37171ce8b
Revises: 67505ba5bb84
Create Date: 2026-11-17 23:02:43.875084

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "18d37171ce8b"
down_revision: Union[str, Sequence[str], None] = "67505ba5bb84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE dishes ADD COLUMN category TEXT;")
    op.execute(
        "ALTER TABLE dishes ADD CONSTRAINT dishes_category_check "
        "CHECK (category IS NULL OR category IN ('Aperitivo','Comida','Postre','Bebida'));"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE dishes DROP CONSTRAINT IF EXISTS dishes_category_check;")
    op.execute("ALTER TABLE dishes DROP COLUMN IF EXISTS category;")