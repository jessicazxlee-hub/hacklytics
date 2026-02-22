from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.group_chat import GroupChatMessage
from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue
from app.models.user import User

CHAT_ENABLED_GROUP_STATUSES = ("confirmed", "scheduled", "completed")


def list_user_group_chats(db: Session, user_id: UUID, *, limit: int, offset: int) -> list[GroupMatch]:
    stmt = (
        select(GroupMatch)
        .join(GroupMatchMember, GroupMatchMember.group_match_id == GroupMatch.id)
        .where(
            GroupMatchMember.user_id == user_id,
            GroupMatchMember.status == "accepted",
            GroupMatch.status.in_(CHAT_ENABLED_GROUP_STATUSES),
        )
        .order_by(GroupMatch.updated_at.desc(), GroupMatch.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_user_group_chat(db: Session, user_id: UUID, group_match_id: UUID) -> GroupMatch | None:
    stmt = (
        select(GroupMatch)
        .join(GroupMatchMember, GroupMatchMember.group_match_id == GroupMatch.id)
        .where(
            GroupMatch.id == group_match_id,
            GroupMatchMember.user_id == user_id,
            GroupMatchMember.status == "accepted",
            GroupMatch.status.in_(CHAT_ENABLED_GROUP_STATUSES),
        )
    )
    return db.scalar(stmt)


def get_group_chat_venue(db: Session, group_match_id: UUID) -> GroupMatchVenue | None:
    stmt = select(GroupMatchVenue).where(GroupMatchVenue.group_match_id == group_match_id)
    return db.scalar(stmt)


def count_accepted_group_members(db: Session, group_match_id: UUID) -> int:
    stmt = select(func.count()).select_from(GroupMatchMember).where(
        GroupMatchMember.group_match_id == group_match_id,
        GroupMatchMember.status == "accepted",
    )
    return int(db.scalar(stmt) or 0)


def list_group_chat_messages(
    db: Session,
    group_match_id: UUID,
    *,
    limit: int,
) -> list[tuple[GroupChatMessage, User]]:
    stmt = (
        select(GroupChatMessage, User)
        .join(User, User.id == GroupChatMessage.sender_user_id)
        .where(GroupChatMessage.group_match_id == group_match_id)
        .order_by(GroupChatMessage.created_at.asc(), GroupChatMessage.id.asc())
        .limit(limit)
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def get_latest_group_chat_message(db: Session, group_match_id: UUID) -> GroupChatMessage | None:
    stmt = (
        select(GroupChatMessage)
        .where(GroupChatMessage.group_match_id == group_match_id)
        .order_by(GroupChatMessage.created_at.desc(), GroupChatMessage.id.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def create_group_chat_message(
    db: Session,
    *,
    group_match_id: UUID,
    sender_user_id: UUID,
    body: str,
) -> GroupChatMessage:
    message = GroupChatMessage(
        group_match_id=group_match_id,
        sender_user_id=sender_user_id,
        body=body,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def sort_groups_by_latest_activity(
    db: Session,
    groups: Sequence[GroupMatch],
) -> list[GroupMatch]:
    latest_map: dict[UUID, object] = {}
    for group in groups:
        latest = get_latest_group_chat_message(db, group.id)
        latest_map[group.id] = latest.created_at if latest is not None else None

    return sorted(
        groups,
        key=lambda group: (
            latest_map.get(group.id) or group.updated_at or group.created_at,
            group.created_at,
            str(group.id),
        ),
        reverse=True,
    )
