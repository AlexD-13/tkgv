from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.audit import AdminAuditRead


async def list_recent(db: AsyncSession, limit: int = 100) -> list[AdminAuditRead]:
    result = await db.execute(
        text(
            "SELECT id, token_label, method, path, status_code, ip, created_at "
            "FROM admin_audit_log ORDER BY created_at DESC, id DESC LIMIT :limit"
        ),
        {"limit": limit},
    )
    rows = result.mappings().all()
    return [
        AdminAuditRead(
            id=r["id"],
            token_label=r["token_label"],
            method=r["method"],
            path=r["path"],
            status_code=r["status_code"],
            ip=r["ip"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
