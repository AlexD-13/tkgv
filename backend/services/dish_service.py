from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.dish import DishCreate, DishUpdate, DishPublic, DishAdmin


async def _count_registrations(db: AsyncSession, dish_id: int) -> int:
    result = await db.execute(
        text("SELECT COUNT(*) FROM registrations WHERE dish_id = :id"), {"id": dish_id}
    )
    return int(result.scalar_one())


async def _fetch_dish_row(db: AsyncSession, dish_id: int):
    result = await db.execute(
        text(
            "SELECT id, name, description, min_quota, max_quota, tested, active, "
            "created_at, updated_at FROM dishes WHERE id = :id"
        ),
        {"id": dish_id},
    )
    return result.mappings().first()


async def list_public(db: AsyncSession) -> list[DishPublic]:
    result = await db.execute(
        text("SELECT id, name, description, max_quota FROM dishes WHERE active = TRUE ORDER BY id")
    )
    rows = result.mappings().all()
    out: list[DishPublic] = []
    for r in rows:
        registered = await _count_registrations(db, r["id"])
        out.append(
            DishPublic(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                registered=registered,
                max_quota=r["max_quota"],
                is_full=registered >= r["max_quota"],
            )
        )
    return out


async def list_admin(db: AsyncSession) -> list[DishAdmin]:
    result = await db.execute(
        text(
            "SELECT id, name, description, min_quota, max_quota, tested, active, "
            "created_at, updated_at FROM dishes ORDER BY id"
        )
    )
    rows = result.mappings().all()
    out: list[DishAdmin] = []
    for r in rows:
        registered = await _count_registrations(db, r["id"])
        out.append(
            DishAdmin(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                min_quota=r["min_quota"],
                max_quota=r["max_quota"],
                tested=bool(r["tested"]),
                active=bool(r["active"]),
                registered=registered,
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
        )
    return out


async def get_admin(db: AsyncSession, dish_id: int) -> DishAdmin | None:
    r = await _fetch_dish_row(db, dish_id)
    if r is None:
        return None
    registered = await _count_registrations(db, dish_id)
    return DishAdmin(
        id=r["id"],
        name=r["name"],
        description=r["description"],
        min_quota=r["min_quota"],
        max_quota=r["max_quota"],
        tested=bool(r["tested"]),
        active=bool(r["active"]),
        registered=registered,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


async def create_dish(db: AsyncSession, data: DishCreate, commit: bool = True) -> DishAdmin:
    result = await db.execute(
        text(
            "INSERT INTO dishes (name, description, min_quota, max_quota, tested, active) "
            "VALUES (:name, :description, :min_quota, :max_quota, :tested, :active) "
            "RETURNING id"
        ),
        {
            "name": data.name,
            "description": data.description,
            "min_quota": data.min_quota,
            "max_quota": data.max_quota,
            "tested": data.tested,
            "active": data.active,
        },
    )
    if commit:
        await db.commit()
    new_id = result.scalar_one()
    return await get_admin(db, int(new_id))


async def update_dish(db: AsyncSession, dish_id: int, data: DishUpdate) -> DishAdmin | None:
    fields = data.model_dump(exclude_unset=True)
    if not fields:
        return await get_admin(db, dish_id)

    allowed = {"name", "description", "min_quota", "max_quota", "tested", "active"}
    sets: list[str] = []
    params: dict = {"id": dish_id}
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key in ("tested", "active"):
            value = bool(value)
        sets.append(f"{key} = :{key}")
        params[key] = value

    if not sets:
        return await get_admin(db, dish_id)

    result = await db.execute(
        text(f"UPDATE dishes SET {', '.join(sets)} WHERE id = :id"), params
    )
    await db.commit()
    if result.rowcount == 0:
        return None
    return await get_admin(db, dish_id)


async def deactivate_dish(db: AsyncSession, dish_id: int) -> bool:
    result = await db.execute(
        text("UPDATE dishes SET active = FALSE WHERE id = :id"), {"id": dish_id}
    )
    await db.commit()
    return result.rowcount > 0
