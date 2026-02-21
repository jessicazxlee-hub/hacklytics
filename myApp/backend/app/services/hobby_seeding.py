import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.crud.hobby import upsert_hobbies
from app.schemas.hobby import HobbyCreate, HobbySeedResult


def seed_hobby_catalog(db: Session, seed_file: str = "seed/hobbies.json") -> HobbySeedResult:
    path = Path(seed_file)
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {seed_file}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    hobbies = [HobbyCreate(**item) for item in raw]
    created, updated = upsert_hobbies(db, hobbies)
    return HobbySeedResult(created=created, updated=updated, total_input=len(hobbies))
