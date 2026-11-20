from datetime import datetime

from pydantic import BaseModel


class AdminAuditRead(BaseModel):
    id: int
    token_label: str
    method: str
    path: str
    status_code: int
    ip: str | None = None
    created_at: datetime
