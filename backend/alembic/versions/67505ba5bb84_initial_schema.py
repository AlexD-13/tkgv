"""initial_schema

Revision ID: 67505ba5bb84
Revises:
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "67505ba5bb84"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            min_quota INTEGER NOT NULL DEFAULT 0,
            max_quota INTEGER NOT NULL DEFAULT 5,
            tested INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    op.execute(
        """
        CREATE TABLE registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            client_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    op.execute("CREATE INDEX idx_reg_dish ON registrations(dish_id);")
    op.execute(
        """
        CREATE TABLE proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','approved','rejected')),
            reviewed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    op.execute("CREATE INDEX idx_prop_status ON proposals(status);")
    op.execute(
        """
        CREATE TRIGGER dishes_updated_at
        AFTER UPDATE ON dishes
        FOR EACH ROW
        BEGIN
            UPDATE dishes SET updated_at = datetime('now') WHERE id = OLD.id;
        END;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS dishes_updated_at;")
    op.execute("DROP TABLE IF EXISTS proposals;")
    op.execute("DROP TABLE IF EXISTS registrations;")
    op.execute("DROP TABLE IF EXISTS dishes;")
