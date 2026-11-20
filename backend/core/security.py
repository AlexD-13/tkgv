from fastapi import Depends, HTTPException, Request, status

from core.config import ADMIN_TOKEN, ADMIN_TOKENS


def _extract_token(request: Request) -> str | None:
    token = request.headers.get("X-Admin-Token")
    if token:
        return token
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return request.cookies.get("admin_token")


def admin_token_label(token: str | None) -> str | None:
    if not token:
        return None
    return ADMIN_TOKENS.get(token)


async def require_admin(request: Request) -> str:
    if not ADMIN_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin access is not configured",
        )
    token = _extract_token(request)
    label = admin_token_label(token)
    if label is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )
    request.state.admin_label = label
    return label
