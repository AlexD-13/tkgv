"""Seed the dishes table from backend/seeds/seed_dishes.sql.

Usage (from backend/):
    uv run python scripts/run_seed.py            # skip if dishes already exist
    uv run python scripts/run_seed.py --force    # insert even if rows exist
"""
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import DATABASE_URL


SEED_FILE = Path(__file__).resolve().parent.parent / "seeds" / "seed_dishes.sql"


async def main(force: bool) -> None:
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as conn:
            existing = (await conn.execute(text("SELECT COUNT(*) FROM dishes"))).scalar_one()
            if existing and not force:
                print(f"dishes already has {existing} rows; nothing to do (use --force).")
                return
            sql = SEED_FILE.read_text(encoding="utf-8")
            # Strip the transaction wrappers; engine.begin() already wraps.
            sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
            # Drop comment lines.
            sql = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            # Re-include comment-only filtering: drop pure comment lines already handled above.
            for stmt in statements:
                await conn.execute(text(stmt))
            print(f"Seed applied: {len(statements)} INSERT statements.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main("--force" in sys.argv))