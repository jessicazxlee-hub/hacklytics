from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.models.restaurant_rating import RestaurantRating
from app.schemas.restaurant_rating import RestaurantRatingUpsert


def get_restaurant_rating(db: Session, *, user_id: UUID, restaurant_id: int) -> RestaurantRating | None:
    stmt = select(RestaurantRating).where(
        RestaurantRating.user_id == user_id,
        RestaurantRating.restaurant_id == restaurant_id,
    )
    return db.scalar(stmt)


def upsert_restaurant_rating(
    db: Session,
    *,
    user_id: UUID,
    restaurant_id: int,
    payload: RestaurantRatingUpsert,
) -> tuple[RestaurantRating, bool]:
    existing = get_restaurant_rating(db, user_id=user_id, restaurant_id=restaurant_id)
    if existing is None:
        rating = RestaurantRating(
            user_id=user_id,
            restaurant_id=restaurant_id,
            **payload.model_dump(),
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating, True

    update_data = payload.model_dump()
    for field, value in update_data.items():
        setattr(existing, field, value)
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing, False


def list_user_restaurant_ratings(db: Session, *, user_id: UUID) -> list[tuple[RestaurantRating, Restaurant]]:
    stmt = (
        select(RestaurantRating, Restaurant)
        .join(Restaurant, Restaurant.id == RestaurantRating.restaurant_id)
        .where(RestaurantRating.user_id == user_id)
        .order_by(RestaurantRating.updated_at.desc(), RestaurantRating.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]
