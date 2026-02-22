from collections.abc import Generator

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token, verify_firebase_id_token
from app.db.session import SessionLocal

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


def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )
