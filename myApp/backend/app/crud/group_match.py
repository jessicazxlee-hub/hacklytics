from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue
from app.models.user import User

TERMINAL_GROUP_STATUSES = {"cancelled", "expired", "completed"}
ACTIVE_MEMBER_STATUSES = {"invited", "accepted"}


def list_group_matches_for_user(
    db: Session,
    user_id: UUID,
    *,
    limit: int,
    offset: int,
    include_inactive_memberships: bool = False,
) -> list[GroupMatch]:
    stmt = (
        select(GroupMatch)
        .join(GroupMatchMember, GroupMatchMember.group_match_id == GroupMatch.id)
        .where(GroupMatchMember.user_id == user_id)
    )
    if not include_inactive_memberships:
        stmt = stmt.where(GroupMatchMember.status.in_(list(ACTIVE_MEMBER_STATUSES)))
    stmt = stmt.order_by(GroupMatch.updated_at.desc(), GroupMatch.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_group_match_for_user(db: Session, group_match_id: UUID, user_id: UUID) -> GroupMatch | None:
    stmt = (
        select(GroupMatch)
        .join(GroupMatchMember, GroupMatchMember.group_match_id == GroupMatch.id)
        .where(GroupMatch.id == group_match_id, GroupMatchMember.user_id == user_id)
    )
    return db.scalar(stmt)


def get_group_member_for_user(db: Session, group_match_id: UUID, user_id: UUID) -> GroupMatchMember | None:
    stmt = select(GroupMatchMember).where(
        GroupMatchMember.group_match_id == group_match_id,
        GroupMatchMember.user_id == user_id,
    )
    return db.scalar(stmt)


def list_group_members_with_users(db: Session, group_match_id: UUID) -> list[tuple[GroupMatchMember, User]]:
    stmt = (
        select(GroupMatchMember, User)
        .join(User, User.id == GroupMatchMember.user_id)
        .where(GroupMatchMember.group_match_id == group_match_id)
        .order_by(
            GroupMatchMember.slot_number.asc().nulls_last(),
            GroupMatchMember.created_at.asc(),
        )
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def get_group_match_venue(db: Session, group_match_id: UUID) -> GroupMatchVenue | None:
    stmt = select(GroupMatchVenue).where(GroupMatchVenue.group_match_id == group_match_id)
    return db.scalar(stmt)


def get_group_member_counts(db: Session, group_match_id: UUID) -> dict[str, int]:
    stmt = select(GroupMatchMember.status).where(GroupMatchMember.group_match_id == group_match_id)
    counts = Counter(db.scalars(stmt).all())
    return dict(counts)


def set_group_member_status(db: Session, member: GroupMatchMember, status: str) -> GroupMatchMember:
    now = datetime.now(timezone.utc)
    member.status = status
    if status == "accepted":
        member.responded_at = now
        if member.joined_at is None:
            member.joined_at = now
    elif status == "declined":
        member.responded_at = now
    elif status == "left":
        member.left_at = now
    db.add(member)
    return member


def sync_group_match_status(db: Session, group: GroupMatch) -> GroupMatch:
    if group.status in TERMINAL_GROUP_STATUSES:
        return group

    counts = get_group_member_counts(db, group.id)
    accepted_count = counts.get("accepted", 0)
    venue_exists = get_group_match_venue(db, group.id) is not None

    can_be_confirmed = accepted_count >= 4 and (group.group_match_mode == "chat_only" or venue_exists)

    if can_be_confirmed and group.status == "forming":
        group.status = "confirmed"
        if group.chat_room_key is None:
            group.chat_room_key = f"group-{group.id}"
        db.add(group)
        return group

    if group.status == "confirmed" and accepted_count < 4:
        group.status = "forming"
        db.add(group)
        return group

    return group


def commit_group_member_action(db: Session, group: GroupMatch, member: GroupMatchMember) -> tuple[GroupMatch, GroupMatchMember]:
    db.add(member)
    db.add(group)
    db.flush()
    sync_group_match_status(db, group)
    db.commit()
    db.refresh(group)
    db.refresh(member)
    return group, member
