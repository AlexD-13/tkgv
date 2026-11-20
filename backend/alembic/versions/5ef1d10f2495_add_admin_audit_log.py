"""add_admin_audit_log

Revision ID: 5ef1d10f2495
Revises: a215ec3895d2
Create Date: 2026-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "5ef1d10f2495"
down_revision: Union[str, Sequence[str], None] = "a215ec3895d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id BIGSERIAL PRIMARY KEY,
            token_label TEXT NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            ip TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_log (created_at);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_admin_audit_created;")
    op.execute("DROP TABLE IF EXISTS admin_audit_log;")
