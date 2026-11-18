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
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            min_quota INTEGER NOT NULL DEFAULT 0,
            max_quota INTEGER NOT NULL DEFAULT 5,
            tested BOOLEAN NOT NULL DEFAULT FALSE,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    op.execute(
        """
        CREATE TABLE registrations (
            id BIGSERIAL PRIMARY KEY,
            dish_id BIGINT NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            client_id TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    op.execute("CREATE INDEX idx_reg_dish ON registrations(dish_id);")
    op.execute(
        """
        CREATE TABLE proposals (
            id BIGSERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','approved','rejected')),
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    op.execute("CREATE INDEX idx_prop_status ON proposals(status);")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_dishes_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER dishes_updated_at
        BEFORE UPDATE ON dishes
        FOR EACH ROW
        EXECUTE FUNCTION set_dishes_updated_at();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS dishes_updated_at ON dishes;")
    op.execute("DROP FUNCTION IF EXISTS set_dishes_updated_at();")
    op.execute("DROP TABLE IF EXISTS proposals;")
    op.execute("DROP TABLE IF EXISTS registrations;")
    op.execute("DROP TABLE IF EXISTS dishes;")
