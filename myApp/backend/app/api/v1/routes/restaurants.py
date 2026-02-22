from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_db
from app.crud import restaurant as crud_restaurant
from app.crud import restaurant_rating as crud_restaurant_rating
from app.models.user import User
from app.schemas.restaurant import RestaurantCreate, RestaurantRead
from app.schemas.restaurant_rating import RestaurantRatingRead, RestaurantRatingUpsert

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("", response_model=list[RestaurantRead])
def list_restaurants(db: Session = Depends(get_db)) -> list[RestaurantRead]:
    return crud_restaurant.list_restaurants(db)


@router.get("/{restaurant_id}", response_model=RestaurantRead)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)) -> RestaurantRead:
    restaurant = crud_restaurant.get_restaurant(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


@router.post("", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED)
def create_restaurant(payload: RestaurantCreate, db: Session = Depends(get_db)) -> RestaurantRead:
    return crud_restaurant.create_restaurant(db, payload)


@router.post("/{restaurant_id}/rating", response_model=RestaurantRatingRead, status_code=status.HTTP_201_CREATED)
def upsert_my_restaurant_rating(
    restaurant_id: int,
    payload: RestaurantRatingUpsert,
    response: Response,
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> RestaurantRatingRead:
    restaurant = crud_restaurant.get_restaurant(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    rating, created = crud_restaurant_rating.upsert_restaurant_rating(
        db,
        user_id=current_user.id,
        restaurant_id=restaurant_id,
        payload=payload,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
    return RestaurantRatingRead.model_validate(rating)
