from datetime import datetime

from pydantic import BaseModel, Field


class DishBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    category: str | None = None
    min_quota: int = Field(default=0, ge=0)
    max_quota: int = Field(default=5, ge=1)
    tested: bool = False
    active: bool = True


class DishCreate(DishBase):
    pass


class DishUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    category: str | None = None
    min_quota: int | None = Field(default=None, ge=0)
    max_quota: int | None = Field(default=None, ge=1)
    tested: bool | None = None
    active: bool | None = None


class DishPublic(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    registered: int
    max_quota: int
    is_full: bool


class DishAdmin(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    min_quota: int
    max_quota: int
    tested: bool
    active: bool
    registered: int
    created_at: str
    updated_at: str


class DishOccupancy(BaseModel):
    dish_id: int
    registered: int
    max_quota: int
