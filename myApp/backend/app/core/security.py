import json
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def verify_firebase_id_token(token: str) -> dict | None:
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth
        from firebase_admin import credentials
    except ImportError:
        return None

    try:
        firebase_admin.get_app()
    except ValueError:
        service_account_json = os.getenv("SERVICE_ACCOUNT_JSON")
        if service_account_json:
            try:
                info = json.loads(service_account_json)
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except (json.JSONDecodeError, ValueError):
                return None
        else:
            try:
                firebase_admin.initialize_app()
            except ValueError:
                return None

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:  # noqa: BLE001
        return None

    uid = decoded.get("uid")
    if not uid:
        return None

    return {
        "uid": uid,
        "email": decoded.get("email"),
        "email_verified": bool(decoded.get("email_verified", False)),
    }
