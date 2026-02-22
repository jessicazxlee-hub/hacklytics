from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_db
from app.crud import group_match as crud_group_match
from app.models.user import User
from app.schemas.group_match import (
    GroupMatchMemberRead,
    GroupMatchMemberUserRead,
    GroupMatchRead,
    GroupMatchVenueRead,
)

router = APIRouter(prefix="/group-matches", tags=["group-matches"])


def _to_group_match_read(db: Session, group, *, current_user_id: UUID) -> GroupMatchRead:
    member_rows = crud_group_match.list_group_members_with_users(db, group.id)
    members = [
        GroupMatchMemberRead(
            id=member.id,
            user_id=member.user_id,
            status=member.status,
            slot_number=member.slot_number,
            invited_at=member.invited_at,
            responded_at=member.responded_at,
            joined_at=member.joined_at,
            left_at=member.left_at,
            user=GroupMatchMemberUserRead(
                id=user.id,
                display_name=user.display_name,
                neighborhood=user.neighborhood,
            ),
        )
        for member, user in member_rows
    ]

    my_member = next((member for member, _user in member_rows if member.user_id == current_user_id), None)
    if my_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group match not found")

    venue = crud_group_match.get_group_match_venue(db, group.id)
    venue_read = None
    if venue is not None:
        venue_read = GroupMatchVenueRead(
            id=venue.id,
            venue_kind=venue.venue_kind,
            source=venue.source,
            restaurant_id=venue.restaurant_id,
            external_place_id=venue.external_place_id,
            name_snapshot=venue.name_snapshot,
            address_snapshot=venue.address_snapshot,
            neighborhood_snapshot=venue.neighborhood_snapshot,
            price_level=venue.price_level,
        )

    return GroupMatchRead(
        id=group.id,
        status=group.status,
        group_match_mode=group.group_match_mode,
        created_source=group.created_source,
        created_by_user_id=group.created_by_user_id,
        chat_room_key=group.chat_room_key,
        scheduled_for=group.scheduled_for,
        expires_at=group.expires_at,
        member_counts=crud_group_match.get_group_member_counts(db, group.id),
        my_member_status=my_member.status,
        members=members,
        venue=venue_read,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


def _load_group_and_member_or_404(db: Session, *, group_match_id: UUID, user_id: UUID):
    group = crud_group_match.get_group_match_for_user(db, group_match_id, user_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group match not found")
    member = crud_group_match.get_group_member_for_user(db, group_match_id, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group match not found")
    return group, member


@router.get("", response_model=list[GroupMatchRead])
def list_group_matches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_inactive_memberships: bool = Query(default=False),
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[GroupMatchRead]:
    groups = crud_group_match.list_group_matches_for_user(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        include_inactive_memberships=include_inactive_memberships,
    )
    return [_to_group_match_read(db, group, current_user_id=current_user.id) for group in groups]


@router.get("/{group_match_id}", response_model=GroupMatchRead)
def get_group_match(
    group_match_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> GroupMatchRead:
    group = crud_group_match.get_group_match_for_user(db, group_match_id, current_user.id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group match not found")
    return _to_group_match_read(db, group, current_user_id=current_user.id)


@router.post("/{group_match_id}/accept", response_model=GroupMatchRead)
def accept_group_match_invite(
    group_match_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> GroupMatchRead:
    group, member = _load_group_and_member_or_404(db, group_match_id=group_match_id, user_id=current_user.id)
    if group.status in {"cancelled", "expired", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group match is not active")
    if member.status != "invited":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership is not invited")

    crud_group_match.set_group_member_status(db, member, "accepted")
    group, _ = crud_group_match.commit_group_member_action(db, group, member)
    return _to_group_match_read(db, group, current_user_id=current_user.id)


@router.post("/{group_match_id}/decline", response_model=GroupMatchRead)
def decline_group_match_invite(
    group_match_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> GroupMatchRead:
    group, member = _load_group_and_member_or_404(db, group_match_id=group_match_id, user_id=current_user.id)
    if group.status in {"cancelled", "expired", "completed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group match is not active")
    if member.status != "invited":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership is not invited")

    crud_group_match.set_group_member_status(db, member, "declined")
    group, _ = crud_group_match.commit_group_member_action(db, group, member)
    return _to_group_match_read(db, group, current_user_id=current_user.id)


@router.post("/{group_match_id}/leave", response_model=GroupMatchRead)
def leave_group_match(
    group_match_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> GroupMatchRead:
    group, member = _load_group_and_member_or_404(db, group_match_id=group_match_id, user_id=current_user.id)
    if group.status in {"cancelled", "expired", "completed", "scheduled"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot leave group in current status")
    if member.status != "accepted":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Membership is not accepted")

    crud_group_match.set_group_member_status(db, member, "left")
    group, _ = crud_group_match.commit_group_member_action(db, group, member)
    return _to_group_match_read(db, group, current_user_id=current_user.id)
