from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.hobby import HobbyCatalog, UserHobby
from app.models.social import FriendRequest, Friendship
from app.models.user import User


def get_friend_request(db: Session, request_id: UUID) -> FriendRequest | None:
    return db.get(FriendRequest, request_id)


def get_pending_friend_request_between(db: Session, user_a_id: UUID, user_b_id: UUID) -> FriendRequest | None:
    stmt = select(FriendRequest).where(
        FriendRequest.status == "pending",
        or_(
            and_(
                FriendRequest.requester_id == user_a_id,
                FriendRequest.addressee_id == user_b_id,
            ),
            and_(
                FriendRequest.requester_id == user_b_id,
                FriendRequest.addressee_id == user_a_id,
            ),
        ),
    )
    return db.scalar(stmt)


def get_directional_friend_request(db: Session, requester_id: UUID, addressee_id: UUID) -> FriendRequest | None:
    stmt = select(FriendRequest).where(
        FriendRequest.requester_id == requester_id,
        FriendRequest.addressee_id == addressee_id,
    )
    return db.scalar(stmt)


def are_friends(db: Session, user_id: UUID, other_user_id: UUID) -> bool:
    stmt = select(Friendship).where(Friendship.user_id == user_id, Friendship.friend_id == other_user_id)
    return db.scalar(stmt) is not None


def create_friend_request(db: Session, requester_id: UUID, addressee_id: UUID) -> FriendRequest:
    friend_request = FriendRequest(requester_id=requester_id, addressee_id=addressee_id)
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    return friend_request


def set_friend_request_status(db: Session, friend_request: FriendRequest, status: str) -> FriendRequest:
    friend_request.status = status
    friend_request.responded_at = datetime.now(timezone.utc)
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    return friend_request


def reopen_friend_request(db: Session, friend_request: FriendRequest) -> FriendRequest:
    friend_request.status = "pending"
    friend_request.responded_at = None
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    return friend_request


def accept_friend_request(db: Session, friend_request: FriendRequest) -> FriendRequest:
    now = datetime.now(timezone.utc)
    friend_request.status = "accepted"
    friend_request.responded_at = now
    db.add(friend_request)

    # Store symmetric rows so friend lookups are simple.
    for left_id, right_id in (
        (friend_request.requester_id, friend_request.addressee_id),
        (friend_request.addressee_id, friend_request.requester_id),
    ):
        existing = db.scalar(
            select(Friendship).where(Friendship.user_id == left_id, Friendship.friend_id == right_id)
        )
        if existing is None:
            db.add(
                Friendship(
                    user_id=left_id,
                    friend_id=right_id,
                    source_request_id=friend_request.id,
                )
            )

    db.commit()
    db.refresh(friend_request)
    return friend_request


def list_incoming_pending_requests(db: Session, user_id: UUID) -> list[tuple[FriendRequest, User]]:
    stmt = (
        select(FriendRequest, User)
        .join(User, FriendRequest.requester_id == User.id)
        .where(FriendRequest.addressee_id == user_id, FriendRequest.status == "pending")
        .order_by(FriendRequest.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def list_outgoing_pending_requests(db: Session, user_id: UUID) -> list[tuple[FriendRequest, User]]:
    stmt = (
        select(FriendRequest, User)
        .join(User, FriendRequest.addressee_id == User.id)
        .where(FriendRequest.requester_id == user_id, FriendRequest.status == "pending")
        .order_by(FriendRequest.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def list_friends(db: Session, user_id: UUID) -> list[tuple[User, datetime]]:
    stmt = (
        select(User, Friendship.created_at)
        .join(Friendship, Friendship.friend_id == User.id)
        .where(Friendship.user_id == user_id)
        .order_by(User.display_name.asc(), User.created_at.asc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def get_related_pending_request_user_ids(db: Session, user_id: UUID) -> set[UUID]:
    stmt = select(FriendRequest.requester_id, FriendRequest.addressee_id).where(
        FriendRequest.status == "pending",
        or_(FriendRequest.requester_id == user_id, FriendRequest.addressee_id == user_id),
    )
    excluded: set[UUID] = set()
    for requester_id, addressee_id in db.execute(stmt).all():
        if requester_id == user_id:
            excluded.add(addressee_id)
        else:
            excluded.add(requester_id)
    return excluded


def get_friend_ids(db: Session, user_id: UUID) -> set[UUID]:
    stmt = select(Friendship.friend_id).where(Friendship.user_id == user_id)
    return set(db.scalars(stmt).all())


def list_discoverable_users_excluding(
    db: Session,
    excluded_ids: set[UUID],
    *,
    limit: int,
    offset: int,
) -> list[User]:
    stmt = select(User).where(User.discoverable.is_(True))
    if excluded_ids:
        stmt = stmt.where(User.id.notin_(list(excluded_ids)))
    stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


def get_user_hobby_codes_map(db: Session, user_ids: list[UUID]) -> dict[UUID, list[str]]:
    if not user_ids:
        return {}

    stmt = (
        select(UserHobby.user_id, HobbyCatalog.code)
        .join(HobbyCatalog, HobbyCatalog.id == UserHobby.hobby_id)
        .where(UserHobby.user_id.in_(user_ids))
        .order_by(UserHobby.user_id.asc(), HobbyCatalog.code.asc())
    )
    hobby_map: dict[UUID, list[str]] = defaultdict(list)
    for user_id, hobby_code in db.execute(stmt).all():
        hobby_map[user_id].append(hobby_code)
    return dict(hobby_map)
