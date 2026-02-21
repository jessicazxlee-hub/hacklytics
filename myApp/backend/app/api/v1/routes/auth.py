from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import user as crud_user
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    existing = crud_user.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = crud_user.create_user(db, payload)
    return user


@router.post("/login", status_code=status.HTTP_410_GONE)
def login(payload: LoginRequest) -> None:  # noqa: ARG001
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Local login is disabled. Use Firebase authentication and send Firebase ID tokens to backend endpoints.",
    )
