from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileBase(BaseModel):
    email: EmailStr
    display_name: str | None = None
    firebase_uid: str | None = None
    auth_provider: str = "firebase"
    email_verified: bool = False

    neighborhood: str | None = None
    geohash: str | None = None

    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)

    diet_tags: list[str] = Field(default_factory=list)
    vibe_tags: list[str] = Field(default_factory=list)

    gender: str | None = None
    birth_year: int | None = Field(default=None, ge=1900)

    discoverable: bool = True
    open_to_meetups: bool = False


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    neighborhood: str | None = None
    geohash: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    diet_tags: list[str] | None = None
    vibe_tags: list[str] | None = None
    gender: str | None = None
    birth_year: int | None = Field(default=None, ge=1900)
    discoverable: bool | None = None
    open_to_meetups: bool | None = None


# Compatibility schema for existing /auth/register route.
# This will be removed when Firebase token verification replaces local auth endpoints.
class UserCreate(UserProfileCreate):
    password: str


class UserRead(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hobbies: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MeProfileUpdate(BaseModel):
    display_name: str | None = None
    neighborhood: str | None = None
    geohash: str | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    diet_tags: list[str] | None = None
    vibe_tags: list[str] | None = None
    gender: str | None = None
    birth_year: int | None = Field(default=None, ge=1900)
    discoverable: bool | None = None
    open_to_meetups: bool | None = None
    hobbies: list[str] | None = None
