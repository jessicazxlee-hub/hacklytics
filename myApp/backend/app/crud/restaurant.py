from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate


def list_restaurants(db: Session) -> list[Restaurant]:
    stmt = select(Restaurant).order_by(Restaurant.id.asc())
    return list(db.scalars(stmt).all())


def get_restaurant(db: Session, restaurant_id: int) -> Restaurant | None:
    stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
    return db.scalar(stmt)


def get_restaurant_by_name_and_address(
    db: Session, name: str, address: str | None
) -> Restaurant | None:
    stmt = select(Restaurant).where(Restaurant.name == name)
    if address is None:
        stmt = stmt.where(Restaurant.address.is_(None))
    else:
        stmt = stmt.where(Restaurant.address == address)
    return db.scalar(stmt)


def create_restaurant(db: Session, restaurant_in: RestaurantCreate) -> Restaurant:
    restaurant = Restaurant(**restaurant_in.model_dump())
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant
