import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.crud.restaurant import create_restaurant
from app.schemas.restaurant import RestaurantCreate


def seed_restaurants(db: Session, seed_file: str = "seed/restaurants.json") -> int:
    path = Path(seed_file)
    if not path.exists():
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for item in data:
        create_restaurant(db, RestaurantCreate(**item))
        count += 1
    return count
