from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserProfileCreate, UserProfileUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> User | None:
    stmt = select(User).where(User.firebase_uid == firebase_uid)
    return db.scalar(stmt)


def get_user_by_subject(db: Session, subject: str) -> User | None:
    user = get_user_by_firebase_uid(db, subject)
    if user is not None:
        return user
    return get_user_by_email(db, subject)


def create_user_profile(db: Session, profile_in: UserProfileCreate) -> User:
    user = User(**profile_in.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, profile_in: UserProfileUpdate) -> User:
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Compatibility helper for existing /auth/register route.
def create_user(db: Session, user_in: UserCreate) -> User:
    profile_data = user_in.model_dump(exclude={"password"})
    if not profile_data.get("firebase_uid"):
        profile_data["firebase_uid"] = f"legacy:{user_in.email.lower()}"

    return create_user_profile(db, UserProfileCreate(**profile_data))


# Temporary compatibility behavior until Firebase auth verification is implemented.
def authenticate_user(db: Session, email: str, password: str) -> User | None:  # noqa: ARG001
    return get_user_by_email(db, email)
