from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GroupMatchVenueRead(BaseModel):
    id: UUID
    venue_kind: str
    source: str
    restaurant_id: int | None = None
    external_place_id: str | None = None
    name_snapshot: str
    address_snapshot: str | None = None
    neighborhood_snapshot: str | None = None
    price_level: int | None = None


class GroupMatchMemberUserRead(BaseModel):
    id: UUID
    display_name: str | None = None
    neighborhood: str | None = None


class GroupMatchMemberRead(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    slot_number: int | None = None
    invited_at: datetime
    responded_at: datetime | None = None
    joined_at: datetime | None = None
    left_at: datetime | None = None
    user: GroupMatchMemberUserRead


class GroupMatchRead(BaseModel):
    id: UUID
    status: str
    group_match_mode: str
    created_source: str
    created_by_user_id: UUID | None = None
    chat_room_key: str | None = None
    scheduled_for: datetime | None = None
    expires_at: datetime | None = None
    member_counts: dict[str, int]
    my_member_status: str
    members: list[GroupMatchMemberRead]
    venue: GroupMatchVenueRead | None = None
    created_at: datetime
    updated_at: datetime
