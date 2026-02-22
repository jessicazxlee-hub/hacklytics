from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_current_user, get_db
from app.crud import hobby as crud_hobby
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import MeProfileUpdate, UserProfileUpdate, UserRead

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def read_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {"sub": current_user["sub"]}


@router.get("/profile", response_model=UserRead)
def read_profile(
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> UserRead:
    hobby_codes = crud_hobby.get_user_hobby_codes(db, current_user.id)
    profile = UserRead.model_validate(current_user).model_copy(update={"hobbies": hobby_codes})
    return profile


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: MeProfileUpdate,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> UserRead:
    update_values = payload.model_dump(exclude_unset=True, exclude={"hobbies"})
    if update_values:
        base_update = UserProfileUpdate(**update_values)
        updated_user = crud_user.update_user_profile(db, current_user, base_update)
    else:
        updated_user = current_user

    if payload.hobbies is not None:
        try:
            crud_hobby.set_user_hobbies_by_codes(db, updated_user.id, payload.hobbies)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    hobby_codes = crud_hobby.get_user_hobby_codes(db, updated_user.id)
    profile = UserRead.model_validate(updated_user).model_copy(update={"hobbies": hobby_codes})
    return profile
