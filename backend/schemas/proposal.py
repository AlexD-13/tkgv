from datetime import datetime

from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    dish_name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ProposalRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    dish_name: str
    description: str | None = None
    status: str
    reviewed_at: datetime | None = None
    created_at: datetime


class ProposalApprove(BaseModel):
    min_quota: int = Field(default=0, ge=0)
    max_quota: int = Field(default=5, ge=1)
    tested: bool = False
