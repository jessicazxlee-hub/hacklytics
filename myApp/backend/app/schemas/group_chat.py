from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GroupChatSenderRead(BaseModel):
    id: UUID
    display_name: str | None = None


class GroupChatMessageRead(BaseModel):
    id: UUID
    group_match_id: UUID
    sender: GroupChatSenderRead
    body: str
    created_at: datetime
    updated_at: datetime


class GroupChatMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class GroupChatLastMessageRead(BaseModel):
    id: UUID
    sender_user_id: UUID
    body_preview: str
    created_at: datetime


class GroupChatSummaryRead(BaseModel):
    id: UUID
    status: str
    group_match_mode: str
    chat_room_key: str | None = None
    member_count: int
    venue_name: str | None = None
    last_message: GroupChatLastMessageRead | None = None
    created_at: datetime
    updated_at: datetime
