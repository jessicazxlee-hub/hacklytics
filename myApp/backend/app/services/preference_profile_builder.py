from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hobby import HobbyCatalog, UserHobby
from app.models.restaurant import Restaurant
from app.models.restaurant_rating import RestaurantRating
from app.models.user import User

PREFERENCE_PROFILE_EMBEDDING_VERSION = "preference_profile_v1"


@dataclass(frozen=True)
class RatedRestaurantSignal:
    restaurant_id: int
    name: str
    cuisine: str | None
    rating: int
    would_return: bool | None


@dataclass(frozen=True)
class PreferenceProfileFeatures:
    hobbies: list[str]
    diet_tags: list[str]
    vibe_tags: list[str]
    liked_cuisines: list[str]
    disliked_cuisines: list[str]
    liked_restaurants: list[RatedRestaurantSignal]
    disliked_restaurants: list[RatedRestaurantSignal]
    rating_count: int
    avg_rating: float | None
    positive_rating_count: int
    negative_rating_count: int


@dataclass(frozen=True)
class PreferenceProfileMetadata:
    user_id: UUID
    discoverable: bool
    open_to_meetups: bool
    neighborhood: str | None
    geohash: str | None
    budget_min: int | None
    budget_max: int | None
    gender: str | None
    birth_year: int | None


@dataclass(frozen=True)
class PreferenceProfile:
    user_id: UUID
    embedding_version: str
    metadata: PreferenceProfileMetadata
    features: PreferenceProfileFeatures
    text_for_embedding: str

    def as_dict(self) -> dict:
        return {
            "user_id": str(self.user_id),
            "embedding_version": self.embedding_version,
            "metadata": asdict(self.metadata),
            "features": {
                **{
                    k: v
                    for k, v in asdict(self.features).items()
                    if k not in {"liked_restaurants", "disliked_restaurants"}
                },
                "liked_restaurants": [asdict(item) for item in self.features.liked_restaurants],
                "disliked_restaurants": [asdict(item) for item in self.features.disliked_restaurants],
            },
            "text_for_embedding": self.text_for_embedding,
        }


def _normalize_list(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values or []:
        cleaned = value.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return sorted(normalized)


def _is_positive_rating(row: RestaurantRating) -> bool:
    return bool(row.rating >= 4 or row.would_return is True)


def _is_negative_rating(row: RestaurantRating) -> bool:
    return bool(row.rating <= 2 or row.would_return is False)


def _load_user_hobby_codes(db: Session, user_id: UUID) -> list[str]:
    stmt = (
        select(HobbyCatalog.code)
        .join(UserHobby, UserHobby.hobby_id == HobbyCatalog.id)
        .where(UserHobby.user_id == user_id)
        .order_by(HobbyCatalog.code.asc())
    )
    return list(db.scalars(stmt).all())


def _load_restaurant_ratings_with_restaurants(
    db: Session, user_id: UUID
) -> list[tuple[RestaurantRating, Restaurant]]:
    stmt = (
        select(RestaurantRating, Restaurant)
        .join(Restaurant, Restaurant.id == RestaurantRating.restaurant_id)
        .where(RestaurantRating.user_id == user_id)
        .order_by(RestaurantRating.updated_at.desc(), RestaurantRating.id.asc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def _restaurant_signal(row: RestaurantRating, restaurant: Restaurant) -> RatedRestaurantSignal:
    return RatedRestaurantSignal(
        restaurant_id=restaurant.id,
        name=restaurant.name,
        cuisine=restaurant.cuisine.strip().lower() if restaurant.cuisine else None,
        rating=row.rating,
        would_return=row.would_return,
    )


def _build_features(user: User, rating_rows: list[tuple[RestaurantRating, Restaurant]], hobby_codes: list[str]) -> PreferenceProfileFeatures:
    ratings_only = [rating for rating, _restaurant in rating_rows]
    avg_rating = round(mean([rating.rating for rating in ratings_only]), 3) if ratings_only else None

    liked_restaurants: list[RatedRestaurantSignal] = []
    disliked_restaurants: list[RatedRestaurantSignal] = []
    liked_cuisines: set[str] = set()
    disliked_cuisines: set[str] = set()

    for rating, restaurant in rating_rows:
        signal = _restaurant_signal(rating, restaurant)
        if _is_positive_rating(rating):
            liked_restaurants.append(signal)
            if signal.cuisine:
                liked_cuisines.add(signal.cuisine)
        elif _is_negative_rating(rating):
            disliked_restaurants.append(signal)
            if signal.cuisine:
                disliked_cuisines.add(signal.cuisine)

    # Stable ordering for deterministic profile text and downstream tests.
    liked_restaurants.sort(key=lambda x: (-x.rating, x.name.lower(), x.restaurant_id))
    disliked_restaurants.sort(key=lambda x: (x.rating, x.name.lower(), x.restaurant_id))

    return PreferenceProfileFeatures(
        hobbies=sorted(hobby_codes),
        diet_tags=_normalize_list(user.diet_tags),
        vibe_tags=_normalize_list(user.vibe_tags),
        liked_cuisines=sorted(liked_cuisines),
        disliked_cuisines=sorted(disliked_cuisines),
        liked_restaurants=liked_restaurants,
        disliked_restaurants=disliked_restaurants,
        rating_count=len(ratings_only),
        avg_rating=avg_rating,
        positive_rating_count=len(liked_restaurants),
        negative_rating_count=len(disliked_restaurants),
    )


def _build_metadata(user: User) -> PreferenceProfileMetadata:
    return PreferenceProfileMetadata(
        user_id=user.id,
        discoverable=user.discoverable,
        open_to_meetups=user.open_to_meetups,
        neighborhood=user.neighborhood.strip() if user.neighborhood else None,
        geohash=user.geohash,
        budget_min=user.budget_min,
        budget_max=user.budget_max,
        gender=user.gender.strip().lower() if user.gender else None,
        birth_year=user.birth_year,
    )


def _csv(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _restaurant_names(values: list[RatedRestaurantSignal]) -> str:
    if not values:
        return "none"
    return ", ".join(item.name for item in values)


def _build_text_for_embedding(metadata: PreferenceProfileMetadata, features: PreferenceProfileFeatures) -> str:
    budget_text = (
        f"{metadata.budget_min}-{metadata.budget_max}"
        if metadata.budget_min is not None and metadata.budget_max is not None
        else "unspecified"
    )
    lines = [
        "Proximity user preference profile",
        f"meetup_mode_preference: {'in_person' if metadata.open_to_meetups else 'chat_only'}",
        f"neighborhood: {metadata.neighborhood or 'unknown'}",
        f"budget_range: {budget_text}",
        f"hobbies: {_csv(features.hobbies)}",
        f"diet_tags: {_csv(features.diet_tags)}",
        f"vibe_tags: {_csv(features.vibe_tags)}",
        f"liked_cuisines: {_csv(features.liked_cuisines)}",
        f"disliked_cuisines: {_csv(features.disliked_cuisines)}",
        f"liked_restaurants: {_restaurant_names(features.liked_restaurants)}",
        f"disliked_restaurants: {_restaurant_names(features.disliked_restaurants)}",
        f"rating_summary: count={features.rating_count}, avg={features.avg_rating if features.avg_rating is not None else 'none'}, positive={features.positive_rating_count}, negative={features.negative_rating_count}",
    ]
    return "\n".join(lines)


def build_preference_profile(db: Session, user_id: UUID) -> PreferenceProfile:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError(f"User not found: {user_id}")

    hobby_codes = _load_user_hobby_codes(db, user.id)
    rating_rows = _load_restaurant_ratings_with_restaurants(db, user.id)

    metadata = _build_metadata(user)
    features = _build_features(user, rating_rows, hobby_codes)
    text_for_embedding = _build_text_for_embedding(metadata, features)

    return PreferenceProfile(
        user_id=user.id,
        embedding_version=PREFERENCE_PROFILE_EMBEDDING_VERSION,
        metadata=metadata,
        features=features,
        text_for_embedding=text_for_embedding,
    )
