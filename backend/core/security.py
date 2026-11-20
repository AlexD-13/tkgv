from fastapi import Depends, HTTPException, Request, status

from core.config import ADMIN_TOKEN


def _extract_token(request: Request) -> str | None:
    token = request.headers.get("X-Admin-Token")
    if token:
        return token
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("admin_token")


async def require_admin(request: Request) -> None:
    if not ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access is not configured",
        )
    if _extract_token(request) != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )
