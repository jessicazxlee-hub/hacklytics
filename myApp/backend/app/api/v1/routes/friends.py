from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_db
from app.crud import social as crud_social
from app.models.user import User
from app.schemas.social import (
    FriendRead,
    FriendRequestCreateResult,
    FriendRequestListItem,
    FriendRequestRead,
    UserPublicRead,
)

router = APIRouter(prefix="/friends", tags=["friends"])


def _request_list_response(db: Session, rows: list[tuple[object, User]]) -> list[FriendRequestListItem]:
    hobby_map = crud_social.get_user_hobby_codes_map(db, [user.id for _, user in rows])
    response: list[FriendRequestListItem] = []
    for request_obj, user in rows:
        response.append(
            FriendRequestListItem(
                request=FriendRequestRead.model_validate(request_obj),
                user=UserPublicRead.model_validate(user).model_copy(update={"hobbies": hobby_map.get(user.id, [])}),
            )
        )
    return response


@router.get("", response_model=list[FriendRead])
def list_friends(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[FriendRead]:
    rows = crud_social.list_friends(db, current_user.id)
    hobby_map = crud_social.get_user_hobby_codes_map(db, [user.id for user, _ in rows])
    return [
        FriendRead(
            user=UserPublicRead.model_validate(user).model_copy(update={"hobbies": hobby_map.get(user.id, [])}),
            friend_since=friend_since,
        )
        for user, friend_since in rows
    ]


@router.get("/requests/incoming", response_model=list[FriendRequestListItem])
def list_incoming_friend_requests(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[FriendRequestListItem]:
    rows = crud_social.list_incoming_pending_requests(db, current_user.id)
    return _request_list_response(db, rows)


@router.get("/requests/outgoing", response_model=list[FriendRequestListItem])
def list_outgoing_friend_requests(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[FriendRequestListItem]:
    rows = crud_social.list_outgoing_pending_requests(db, current_user.id)
    return _request_list_response(db, rows)


@router.post("/requests/{user_id}", response_model=FriendRequestCreateResult, status_code=status.HTTP_201_CREATED)
def create_friend_request(
    user_id: UUID,
    response: Response,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> FriendRequestCreateResult:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send friend request to yourself")

    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not target_user.discoverable:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if crud_social.are_friends(db, current_user.id, target_user.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already friends")

    existing_pending = crud_social.get_pending_friend_request_between(db, current_user.id, target_user.id)
    if existing_pending is not None:
        response.status_code = status.HTTP_200_OK
        base = FriendRequestRead.model_validate(existing_pending)
        return FriendRequestCreateResult(**base.model_dump(), created=False)

    existing_directional = crud_social.get_directional_friend_request(db, current_user.id, target_user.id)
    if existing_directional is not None:
        if existing_directional.status == "accepted":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already friends")
        reopened = crud_social.reopen_friend_request(db, existing_directional)
        base = FriendRequestRead.model_validate(reopened)
        return FriendRequestCreateResult(**base.model_dump(), created=True)

    created = crud_social.create_friend_request(db, requester_id=current_user.id, addressee_id=target_user.id)
    base = FriendRequestRead.model_validate(created)
    return FriendRequestCreateResult(**base.model_dump(), created=True)


@router.post("/requests/{request_id}/accept", response_model=FriendRequestRead)
def accept_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> FriendRequestRead:
    friend_request = crud_social.get_friend_request(db, request_id)
    if friend_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")

    if friend_request.addressee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to accept this request")
    if friend_request.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friend request is not pending")

    accepted = crud_social.accept_friend_request(db, friend_request)
    return FriendRequestRead.model_validate(accepted)


@router.post("/requests/{request_id}/decline", response_model=FriendRequestRead)
def decline_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> FriendRequestRead:
    friend_request = crud_social.get_friend_request(db, request_id)
    if friend_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")

    if friend_request.addressee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to decline this request")
    if friend_request.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friend request is not pending")

    declined = crud_social.set_friend_request_status(db, friend_request, "declined")
    return FriendRequestRead.model_validate(declined)


@router.post("/requests/{request_id}/cancel", response_model=FriendRequestRead)
def cancel_friend_request(
    request_id: UUID,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> FriendRequestRead:
    friend_request = crud_social.get_friend_request(db, request_id)
    if friend_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Friend request not found")

    if friend_request.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to cancel this request")
    if friend_request.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Friend request is not pending")

    cancelled = crud_social.set_friend_request_status(db, friend_request, "cancelled")
    return FriendRequestRead.model_validate(cancelled)
