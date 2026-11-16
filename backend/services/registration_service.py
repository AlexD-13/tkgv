from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.registration import RegistrationCreate, RegistrationRead


async def count_by_dish(db: AsyncSession, dish_id: int) -> int:
    result = await db.execute(
        text("SELECT COUNT(*) FROM registrations WHERE dish_id = :id"), {"id": dish_id}
    )
    return int(result.scalar_one())


async def list_by_client(db: AsyncSession, client_id: str) -> list[RegistrationRead]:
    result = await db.execute(
        text(
            "SELECT id, dish_id, first_name, last_name, client_id, created_at "
            "FROM registrations WHERE client_id = :cid ORDER BY id"
        ),
        {"cid": client_id},
    )
    rows = result.mappings().all()
    return [
        RegistrationRead(
            id=r["id"],
            dish_id=r["dish_id"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            client_id=r["client_id"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


async def list_all(db: AsyncSession) -> list[RegistrationRead]:
    result = await db.execute(
        text(
            "SELECT id, dish_id, first_name, last_name, client_id, created_at "
            "FROM registrations ORDER BY dish_id, id"
        )
    )
    rows = result.mappings().all()
    return [
        RegistrationRead(
            id=r["id"],
            dish_id=r["dish_id"],
            first_name=r["first_name"],
            last_name=r["last_name"],
            client_id=r["client_id"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


async def create_registration(
    db: AsyncSession, data: RegistrationCreate
) -> RegistrationRead:
    # Validate dish existence/active (read-only; the INSERT below is the atomic guard).
    dish_row = (
        await db.execute(
            text("SELECT max_quota, active FROM dishes WHERE id = :id"),
            {"id": data.dish_id},
        )
    ).mappings().first()

    # Atomic quota check + insert in a single statement (RNF-01).
    result = await db.execute(
        text(
            "INSERT INTO registrations (dish_id, first_name, last_name, client_id) "
            "SELECT :dish_id, :first_name, :last_name, :client_id "
            "FROM dishes "
            "WHERE id = :dish_id AND active = 1 "
            "AND (SELECT COUNT(*) FROM registrations WHERE dish_id = :dish_id) "
            "    < max_quota"
        ),
        {
            "dish_id": data.dish_id,
            "first_name": data.first_name,
            "last_name": data.last_name,
            "client_id": data.client_id,
        },
    )
    await db.commit()

    if result.rowcount == 0:
        if dish_row is None or not dish_row["active"]:
            raise ValueError("dish not found or inactive")
        raise ValueError("dish is full")

    new_id = (await db.execute(text("SELECT last_insert_rowid()"))).scalar_one()

    row = (
        await db.execute(
            text(
                "SELECT id, dish_id, first_name, last_name, client_id, created_at "
                "FROM registrations WHERE id = :id"
            ),
            {"id": int(new_id)},
        )
    ).mappings().first()
    return RegistrationRead(
        id=row["id"],
        dish_id=row["dish_id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        client_id=row["client_id"],
        created_at=row["created_at"],
    )


async def delete_registration(db: AsyncSession, registration_id: int) -> bool:
    result = await db.execute(
        text("DELETE FROM registrations WHERE id = :id"), {"id": registration_id}
    )
    await db.commit()
    return result.rowcount > 0


async def reassign_registration(
    db: AsyncSession, registration_id: int, new_dish_id: int
) -> RegistrationRead | None:
    reg_row = (
        await db.execute(
            text("SELECT id, dish_id FROM registrations WHERE id = :id"),
            {"id": registration_id},
        )
    ).mappings().first()
    if reg_row is None:
        return None

    dish_row = (
        await db.execute(
            text("SELECT max_quota, active FROM dishes WHERE id = :id"),
            {"id": new_dish_id},
        )
    ).mappings().first()
    if dish_row is None or not dish_row["active"]:
        raise ValueError("target dish not found or inactive")

    result = await db.execute(
        text(
            "UPDATE registrations SET dish_id = :new "
            "WHERE id = :id AND "
            "(SELECT COUNT(*) FROM registrations WHERE dish_id = :new) "
            "    < (SELECT max_quota FROM dishes WHERE id = :new)"
        ),
        {"new": new_dish_id, "id": registration_id},
    )
    await db.commit()

    if result.rowcount == 0:
        raise ValueError("target dish is full")

    row = (
        await db.execute(
            text(
                "SELECT id, dish_id, first_name, last_name, client_id, created_at "
                "FROM registrations WHERE id = :id"
            ),
            {"id": registration_id},
        )
    ).mappings().first()
    return RegistrationRead(
        id=row["id"],
        dish_id=row["dish_id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        client_id=row["client_id"],
        created_at=row["created_at"],
    )


async def list_attendance_grouped(db: AsyncSession):
    # Returns list of dicts: {dish_id, dish_name, registrations: [RegistrationRead]}
    dishes_result = await db.execute(
        text("SELECT id, name FROM dishes ORDER BY id")
    )
    dishes = dishes_result.mappings().all()
    regs = await list_all(db)
    by_dish: dict[int, list] = {d["id"]: [] for d in dishes}
    for r in regs:
        by_dish.setdefault(r.dish_id, []).append(r)
    out = []
    for d in dishes:
        out.append(
            {
                "dish_id": d["id"],
                "dish_name": d["name"],
                "registrations": by_dish.get(d["id"], []),
            }
        )
    # registrations not tied to a dish (shouldn't happen) grouped under None skipped
    return out
