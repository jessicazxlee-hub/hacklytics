from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.hobby import HobbyCatalog, UserHobby
from app.schemas.hobby import HobbyCreate


def _normalize_code(code: str) -> str:
    return code.strip().lower()


def list_hobbies(db: Session, active_only: bool = False) -> list[HobbyCatalog]:
    stmt = select(HobbyCatalog).order_by(HobbyCatalog.code.asc())
    if active_only:
        stmt = stmt.where(HobbyCatalog.is_active.is_(True))
    return list(db.scalars(stmt).all())


def get_hobbies_by_codes(db: Session, codes: list[str]) -> list[HobbyCatalog]:
    normalized = [_normalize_code(code) for code in codes if code.strip()]
    if not normalized:
        return []
    stmt = select(HobbyCatalog).where(HobbyCatalog.code.in_(normalized))
    return list(db.scalars(stmt).all())


def create_hobby(db: Session, hobby_in: HobbyCreate) -> HobbyCatalog:
    normalized_code = _normalize_code(hobby_in.code)
    existing = db.scalar(select(HobbyCatalog).where(HobbyCatalog.code == normalized_code))
    if existing:
        raise ValueError(f"Hobby code already exists: {normalized_code}")

    hobby = HobbyCatalog(code=normalized_code, label=hobby_in.label.strip(), is_active=hobby_in.is_active)
    db.add(hobby)
    db.commit()
    db.refresh(hobby)
    return hobby


def upsert_hobbies(
    db: Session,
    hobbies: list[HobbyCreate],
) -> tuple[int, int]:
    created = 0
    updated = 0

    for hobby_in in hobbies:
        normalized_code = _normalize_code(hobby_in.code)
        hobby = db.scalar(select(HobbyCatalog).where(HobbyCatalog.code == normalized_code))
        if hobby is None:
            hobby = HobbyCatalog(
                code=normalized_code,
                label=hobby_in.label.strip(),
                is_active=hobby_in.is_active,
            )
            db.add(hobby)
            created += 1
            continue

        changed = False
        if hobby.label != hobby_in.label.strip():
            hobby.label = hobby_in.label.strip()
            changed = True
        if hobby.is_active != hobby_in.is_active:
            hobby.is_active = hobby_in.is_active
            changed = True
        if changed:
            db.add(hobby)
            updated += 1

    db.commit()
    return created, updated


def get_user_hobby_codes(db: Session, user_id: UUID) -> list[str]:
    stmt = (
        select(HobbyCatalog.code)
        .join(UserHobby, UserHobby.hobby_id == HobbyCatalog.id)
        .where(UserHobby.user_id == user_id)
        .order_by(HobbyCatalog.code.asc())
    )
    return list(db.scalars(stmt).all())


def set_user_hobbies_by_codes(db: Session, user_id: UUID, hobby_codes: list[str]) -> list[str]:
    normalized = []
    for code in hobby_codes:
        code_normalized = _normalize_code(code)
        if code_normalized and code_normalized not in normalized:
            normalized.append(code_normalized)

    db.execute(delete(UserHobby).where(UserHobby.user_id == user_id))

    if not normalized:
        db.commit()
        return []

    hobbies = get_hobbies_by_codes(db, normalized)
    hobby_by_code = {hobby.code: hobby for hobby in hobbies}
    missing = [code for code in normalized if code not in hobby_by_code]
    if missing:
        db.rollback()
        raise ValueError(f"Unknown hobby codes: {', '.join(missing)}")

    for code in normalized:
        db.add(UserHobby(user_id=user_id, hobby_id=hobby_by_code[code].id))

    db.commit()
    return normalized
