from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import hobby as crud_hobby
from app.schemas.hobby import HobbyRead

router = APIRouter(prefix="/hobbies", tags=["hobbies"])


@router.get("", response_model=list[HobbyRead])
def list_active_hobbies(db: Session = Depends(get_db)) -> list[HobbyRead]:
    return crud_hobby.list_hobbies(db, active_only=True)
