from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.proposal import ProposalCreate, ProposalRead, ProposalApprove
from services.dish_service import create_dish
from schemas.dish import DishCreate


async def _fetch_proposal(db: AsyncSession, proposal_id: int):
    result = await db.execute(
        text(
            "SELECT id, first_name, last_name, dish_name, description, status, "
            "reviewed_at, created_at FROM proposals WHERE id = :id"
        ),
        {"id": proposal_id},
    )
    return result.mappings().first()


async def create_proposal(db: AsyncSession, data: ProposalCreate) -> ProposalRead:
    result = await db.execute(
        text(
            "INSERT INTO proposals (first_name, last_name, dish_name, description) "
            "VALUES (:first_name, :last_name, :dish_name, :description) "
            "RETURNING id"
        ),
        {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "dish_name": data.dish_name,
            "description": data.description,
        },
    )
    await db.commit()
    new_id = result.scalar_one()
    row = await _fetch_proposal(db, int(new_id))
    return ProposalRead(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        dish_name=row["dish_name"],
        description=row["description"],
        status=row["status"],
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
    )


async def list_pending(db: AsyncSession) -> list[ProposalRead]:
    result = await db.execute(
        text(
            "SELECT id, first_name, last_name, dish_name, description, status, "
            "reviewed_at, created_at FROM proposals WHERE status = 'pending' "
            "ORDER BY id"
        )
    )
    rows = result.mappings().all()
    return [
        ProposalRead(
            id=r["id"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            dish_name=r["dish_name"],
            description=r["description"],
            status=r["status"],
            reviewed_at=r["reviewed_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


async def list_all(db: AsyncSession) -> list[ProposalRead]:
    result = await db.execute(
        text(
            "SELECT id, first_name, last_name, dish_name, description, status, "
            "reviewed_at, created_at FROM proposals ORDER BY id"
        )
    )
    rows = result.mappings().all()
    return [
        ProposalRead(
            id=r["id"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            dish_name=r["dish_name"],
            description=r["description"],
            status=r["status"],
            reviewed_at=r["reviewed_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


async def approve_proposal(
    db: AsyncSession, proposal_id: int, data: ProposalApprove
):
    try:
        row = await _fetch_proposal(db, proposal_id)
        if row is None:
            raise ValueError("proposal not found")
        if row["status"] != "pending":
            raise ValueError("proposal is not pending")

        dish = await create_dish(
            db,
            DishCreate(
                name=row["dish_name"],
                description=row["description"],
                min_quota=data.min_quota,
                max_quota=data.max_quota,
                tested=data.tested,
                active=True,
            ),
            commit=False,
        )

        await db.execute(
            text(
                "UPDATE proposals SET status = 'approved', reviewed_at = :ts "
                "WHERE id = :id"
            ),
            {"ts": datetime.now(timezone.utc).isoformat(), "id": proposal_id},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return dish


async def reject_proposal(db: AsyncSession, proposal_id: int) -> bool:
    result = await db.execute(
        text(
            "UPDATE proposals SET status = 'rejected', reviewed_at = :ts "
            "WHERE id = :id AND status = 'pending'"
        ),
        {"ts": datetime.now(timezone.utc).isoformat(), "id": proposal_id},
    )
    await db.commit()
    return result.rowcount > 0
