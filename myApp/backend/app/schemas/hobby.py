from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HobbyBase(BaseModel):
    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_]+$")
    label: str = Field(min_length=2, max_length=120)
    is_active: bool = True


class HobbyCreate(HobbyBase):
    pass


class HobbyRead(HobbyBase):
    id: UUID
    created_at: datetime


class HobbySeedResult(BaseModel):
    created: int
    updated: int
    total_input: int
