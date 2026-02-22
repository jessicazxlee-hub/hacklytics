from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.crud import hobby as crud_hobby
from app.crud import user as crud_user
from app.schemas.user import MeProfileUpdate, UserProfileCreate, UserProfileUpdate, UserRead

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def read_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {"sub": current_user["sub"]}


@router.get("/profile", response_model=UserRead)
def read_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = _get_or_bootstrap_user(db, current_user)

    hobby_codes = crud_hobby.get_user_hobby_codes(db, user.id)
    profile = UserRead.model_validate(user).model_copy(update={"hobbies": hobby_codes})
    return profile


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: MeProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = _get_or_bootstrap_user(db, current_user)

    update_values = payload.model_dump(exclude_unset=True, exclude={"hobbies"})
    if update_values:
        base_update = UserProfileUpdate(**update_values)
        updated_user = crud_user.update_user_profile(db, user, base_update)
    else:
        updated_user = user

    if payload.hobbies is not None:
        try:
            crud_hobby.set_user_hobbies_by_codes(db, updated_user.id, payload.hobbies)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    hobby_codes = crud_hobby.get_user_hobby_codes(db, updated_user.id)
    profile = UserRead.model_validate(updated_user).model_copy(update={"hobbies": hobby_codes})
    return profile


def _get_or_bootstrap_user(db: Session, current_user: dict):
    user = crud_user.get_user_by_subject(db, current_user["sub"])
    if user is not None:
        return user

    if current_user.get("auth_type") != "firebase":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    email = current_user.get("email")
    firebase_uid = current_user.get("firebase_uid")
    if not email or not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Firebase claims for profile bootstrap",
        )

    existing_by_email = crud_user.get_user_by_email(db, email)
    if existing_by_email is not None:
        existing_by_email.firebase_uid = firebase_uid
        existing_by_email.email_verified = bool(current_user.get("email_verified", False))
        db.add(existing_by_email)
        db.commit()
        db.refresh(existing_by_email)
        return existing_by_email

    profile_in = UserProfileCreate(
        email=email,
        firebase_uid=firebase_uid,
        email_verified=bool(current_user.get("email_verified", False)),
    )
    return crud_user.create_user_profile(db, profile_in)
