from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_db
from app.crud import group_chat as crud_group_chat
from app.models.user import User
from app.schemas.group_chat import (
    GroupChatLastMessageRead,
    GroupChatMessageCreate,
    GroupChatMessageRead,
    GroupChatSenderRead,
    GroupChatSummaryRead,
)

router = APIRouter(prefix="/chats", tags=["chats"])


def _message_read(message_obj, sender: User) -> GroupChatMessageRead:
    return GroupChatMessageRead(
        id=message_obj.id,
        group_match_id=message_obj.group_match_id,
        sender=GroupChatSenderRead(id=sender.id, display_name=sender.display_name),
        body=message_obj.body,
        created_at=message_obj.created_at,
        updated_at=message_obj.updated_at,
    )


def _chat_summary(db: Session, group) -> GroupChatSummaryRead:
    venue = crud_group_chat.get_group_chat_venue(db, group.id)
    last_message = crud_group_chat.get_latest_group_chat_message(db, group.id)
    member_count = crud_group_chat.count_accepted_group_members(db, group.id)

    last_message_read = None
    if last_message is not None:
        preview = last_message.body[:120]
        last_message_read = GroupChatLastMessageRead(
            id=last_message.id,
            sender_user_id=last_message.sender_user_id,
            body_preview=preview,
            created_at=last_message.created_at,
        )

    return GroupChatSummaryRead(
        id=group.id,
        status=group.status,
        group_match_mode=group.group_match_mode,
        chat_room_key=group.chat_room_key,
        member_count=member_count,
        venue_name=venue.name_snapshot if venue is not None else None,
        last_message=last_message_read,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.get("", response_model=list[GroupChatSummaryRead])
def list_group_chats(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[GroupChatSummaryRead]:
    groups = crud_group_chat.list_user_group_chats(db, current_user.id, limit=limit, offset=offset)
    groups = crud_group_chat.sort_groups_by_latest_activity(db, groups)
    return [_chat_summary(db, group) for group in groups]


@router.get("/{group_match_id}/messages", response_model=list[GroupChatMessageRead])
def list_group_chat_messages(
    group_match_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[GroupChatMessageRead]:
    group = crud_group_chat.get_user_group_chat(db, current_user.id, group_match_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found")

    rows = crud_group_chat.list_group_chat_messages(db, group.id, limit=limit)
    return [_message_read(message_obj, sender) for message_obj, sender in rows]


@router.post("/{group_match_id}/messages", response_model=GroupChatMessageRead, status_code=status.HTTP_201_CREATED)
def create_group_chat_message(
    group_match_id: UUID,
    payload: GroupChatMessageCreate,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> GroupChatMessageRead:
    group = crud_group_chat.get_user_group_chat(db, current_user.id, group_match_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found")

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message body cannot be empty")

    message_obj = crud_group_chat.create_group_chat_message(
        db,
        group_match_id=group.id,
        sender_user_id=current_user.id,
        body=body,
    )
    return GroupChatMessageRead(
        id=message_obj.id,
        group_match_id=message_obj.group_match_id,
        sender=GroupChatSenderRead(id=current_user.id, display_name=current_user.display_name),
        body=message_obj.body,
        created_at=message_obj.created_at,
        updated_at=message_obj.updated_at,
    )
