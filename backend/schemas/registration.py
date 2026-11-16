from datetime import datetime

from pydantic import BaseModel, Field


class RegistrationCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    dish_id: int
    client_id: str | None = None


class RegistrationRead(BaseModel):
    id: int
    dish_id: int
    first_name: str
    last_name: str
    client_id: str | None = None
    created_at: str


class RegistrationReassign(BaseModel):
    new_dish_id: int
