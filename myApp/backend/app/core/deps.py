from collections.abc import Generator

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token, verify_firebase_id_token
from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserProfileCreate

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if payload is not None:
        subject = payload.get("sub")
        if subject:
            return {"sub": subject, "auth_type": "local_jwt"}

    firebase_claims = verify_firebase_id_token(token)
    if firebase_claims is not None:
        return {
            "sub": firebase_claims["uid"],
            "firebase_uid": firebase_claims["uid"],
            "email": firebase_claims.get("email"),
            "email_verified": firebase_claims.get("email_verified", False),
            "auth_type": "firebase",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )


def get_current_db_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
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


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )
