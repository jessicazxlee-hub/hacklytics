from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.restaurant import RestaurantRead


class RestaurantRatingUpsert(BaseModel):
    rating: int = Field(ge=1, le=5)
    visited: bool = True
    would_return: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)


class RestaurantRatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    restaurant_id: int
    rating: int
    visited: bool
    would_return: bool | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class RestaurantRatingWithRestaurantRead(RestaurantRatingRead):
    restaurant: RestaurantRead
