"""add_note_to_registrations

Revision ID: a215ec3895d2
Revises: 18d37171ce8b
Create Date: 2026-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a215ec3895d2"
down_revision: Union[str, Sequence[str], None] = "18d37171ce8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE registrations ADD COLUMN IF NOT EXISTS note TEXT;")


def downgrade() -> None:
    op.execute("ALTER TABLE registrations DROP COLUMN IF EXISTS note;")
