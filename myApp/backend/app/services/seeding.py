import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.crud.restaurant import create_restaurant, get_restaurant_by_name_and_address
from app.schemas.restaurant import RestaurantCreate


def seed_restaurants(db: Session, seed_file: str = "seed/restaurants.json") -> int:
    path = Path(seed_file)
    if not path.exists():
        return 0

    data = json.loads(path.read_text(encoding="utf-8"))
    count = 0
    for item in data:
        restaurant_in = RestaurantCreate(**item)
        existing = get_restaurant_by_name_and_address(
            db, restaurant_in.name, restaurant_in.address
        )
        if existing is not None:
            continue
        create_restaurant(db, restaurant_in)
        count += 1
    return count
