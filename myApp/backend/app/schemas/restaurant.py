from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RestaurantBase(BaseModel):
    name: str
    cuisine: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantRead(RestaurantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
