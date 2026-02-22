from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None = None
    neighborhood: str | None = None
    discoverable: bool
    open_to_meetups: bool
    hobbies: list[str] = Field(default_factory=list)


class FriendRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    addressee_id: UUID
    status: str
    responded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class FriendRequestCreateResult(FriendRequestRead):
    created: bool


class FriendRequestListItem(BaseModel):
    request: FriendRequestRead
    user: UserPublicRead


class FriendRead(BaseModel):
    user: UserPublicRead
    friend_since: datetime


class MatchSignals(BaseModel):
    same_neighborhood: bool
    hobby_overlap_count: int
    overlap_hobbies: list[str] = Field(default_factory=list)


class MatchRead(BaseModel):
    user: UserPublicRead
    score: int
    signals: MatchSignals
