from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin_key
from app.crud import hobby as crud_hobby
from app.schemas.hobby import HobbyCreate, HobbyRead, HobbySeedResult
from app.services.hobby_seeding import seed_hobby_catalog

router = APIRouter(
    prefix="/admin/hobbies",
    tags=["admin-hobbies"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("", response_model=list[HobbyRead])
def list_hobbies(db: Session = Depends(get_db)) -> list[HobbyRead]:
    return crud_hobby.list_hobbies(db, active_only=False)


@router.post("", response_model=HobbyRead, status_code=status.HTTP_201_CREATED)
def create_hobby(payload: HobbyCreate, db: Session = Depends(get_db)) -> HobbyRead:
    try:
        return crud_hobby.create_hobby(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/seed", response_model=HobbySeedResult)
def seed_hobbies(db: Session = Depends(get_db)) -> HobbySeedResult:
    try:
        return seed_hobby_catalog(db)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
