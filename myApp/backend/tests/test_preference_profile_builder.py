from uuid import UUID, uuid4

from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token
from app.services.preference_profile_builder import (
    PREFERENCE_PROFILE_EMBEDDING_VERSION,
    build_preference_profile,
)


def _register_user(client, *, suffix: str, neighborhood: str = "Downtown"):
    firebase_uid = f"firebase-{suffix}"
    payload = {
        "email": f"{suffix}@example.com",
        "password": "password123",
        "firebase_uid": firebase_uid,
        "neighborhood": neighborhood,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    token = create_access_token(subject=firebase_uid)
    headers = {"Authorization": f"Bearer {token}"}
    return response.json(), headers


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": settings.admin_api_key}


def test_build_preference_profile_includes_profile_hobbies_and_rating_signals(client, test_engine):
    suffix = uuid4().hex[:8]
    user, headers = _register_user(client, suffix=f"pref-{suffix}", neighborhood="Downtown")

    # Controlled hobbies
    for code, label in (
        (f"coffee_{suffix}", "Coffee"),
        (f"hiking_{suffix}", "Hiking"),
    ):
        created = client.post(
            "/api/v1/admin/hobbies",
            json={"code": code, "label": label, "is_active": True},
            headers=_admin_headers(),
        )
        assert created.status_code == 201, created.text

    patch = client.patch(
        "/api/v1/me/profile",
        json={
            "display_name": "Alex",
            "hobbies": [f"hiking_{suffix}", f"coffee_{suffix}"],
            "diet_tags": ["Vegetarian"],
            "vibe_tags": ["Cozy", "Quiet"],
            "open_to_meetups": True,
            "budget_min": 10,
            "budget_max": 35,
        },
        headers=headers,
    )
    assert patch.status_code == 200, patch.text

    # Restaurants + ratings
    cafe = client.post(
        "/api/v1/restaurants",
        json={"name": f"Cafe {suffix}", "cuisine": "Cafe", "address": "1 Main"},
    )
    sushi = client.post(
        "/api/v1/restaurants",
        json={"name": f"Sushi {suffix}", "cuisine": "Japanese", "address": "2 Main"},
    )
    burgers = client.post(
        "/api/v1/restaurants",
        json={"name": f"Burger {suffix}", "cuisine": "Burgers", "address": "3 Main"},
    )
    assert cafe.status_code == 201 and sushi.status_code == 201 and burgers.status_code == 201
    cafe_id = cafe.json()["id"]
    sushi_id = sushi.json()["id"]
    burgers_id = burgers.json()["id"]

    r1 = client.post(
        f"/api/v1/restaurants/{cafe_id}/rating",
        json={"rating": 5, "visited": True, "would_return": True, "notes": "great"},
        headers=headers,
    )
    r2 = client.post(
        f"/api/v1/restaurants/{sushi_id}/rating",
        json={"rating": 4, "visited": True, "would_return": True},
        headers=headers,
    )
    r3 = client.post(
        f"/api/v1/restaurants/{burgers_id}/rating",
        json={"rating": 2, "visited": True, "would_return": False},
        headers=headers,
    )
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)
    assert r3.status_code in (200, 201)

    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as db:
        profile = build_preference_profile(db, UUID(user["id"]))

    assert profile.embedding_version == PREFERENCE_PROFILE_EMBEDDING_VERSION
    assert profile.metadata.user_id == UUID(user["id"])
    assert profile.metadata.open_to_meetups is True
    assert profile.metadata.neighborhood == "Downtown"
    assert profile.metadata.budget_min == 10
    assert profile.metadata.budget_max == 35

    assert profile.features.hobbies == sorted([f"coffee_{suffix}", f"hiking_{suffix}"])
    assert profile.features.diet_tags == ["vegetarian"]
    assert profile.features.vibe_tags == ["cozy", "quiet"]
    assert profile.features.rating_count == 3
    assert profile.features.positive_rating_count == 2
    assert profile.features.negative_rating_count == 1
    assert profile.features.liked_cuisines == ["cafe", "japanese"]
    assert profile.features.disliked_cuisines == ["burgers"]
    assert [item.name for item in profile.features.liked_restaurants] == [f"Cafe {suffix}", f"Sushi {suffix}"]
    assert [item.name for item in profile.features.disliked_restaurants] == [f"Burger {suffix}"]

    text = profile.text_for_embedding
    assert "Proximity user preference profile" in text
    assert "meetup_mode_preference: in_person" in text
    assert f"hobbies: coffee_{suffix}, hiking_{suffix}" in text
    assert "liked_cuisines: cafe, japanese" in text
    assert "disliked_cuisines: burgers" in text
    assert f"liked_restaurants: Cafe {suffix}, Sushi {suffix}" in text
    assert f"disliked_restaurants: Burger {suffix}" in text


def test_build_preference_profile_handles_missing_user(client, test_engine):
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as db:
        try:
            build_preference_profile(db, UUID("00000000-0000-0000-0000-000000000001"))
        except ValueError as exc:
            assert "User not found" in str(exc)
        else:
            raise AssertionError("Expected ValueError for missing user")
