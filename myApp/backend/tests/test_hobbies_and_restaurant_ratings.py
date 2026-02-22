from uuid import uuid4

from app.core.config import settings
from app.core.security import create_access_token


def _register_user(client, *, suffix: str):
    firebase_uid = f"firebase-{suffix}"
    payload = {
        "email": f"{suffix}@example.com",
        "password": "password123",
        "firebase_uid": firebase_uid,
        "neighborhood": "Downtown",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    token = create_access_token(subject=firebase_uid)
    return response.json(), {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": settings.admin_api_key}


def test_public_hobbies_lists_active_only(client):
    create_one = client.post(
        "/api/v1/admin/hobbies",
        json={"code": "active_hobby", "label": "Active Hobby", "is_active": True},
        headers=_admin_headers(),
    )
    create_two = client.post(
        "/api/v1/admin/hobbies",
        json={"code": "inactive_hobby", "label": "Inactive Hobby", "is_active": False},
        headers=_admin_headers(),
    )
    assert create_one.status_code == 201
    assert create_two.status_code == 201

    response = client.get("/api/v1/hobbies")
    assert response.status_code == 200, response.text
    body = response.json()
    codes = [item["code"] for item in body]
    assert "active_hobby" in codes
    assert "inactive_hobby" not in codes


def test_restaurant_rating_upsert_and_me_list(client):
    suffix = uuid4().hex[:8]
    _user, headers = _register_user(client, suffix=f"ratings-{suffix}")

    create_restaurant = client.post(
        "/api/v1/restaurants",
        json={
            "name": f"Test Cafe {suffix}",
            "cuisine": "Cafe",
            "address": "123 Main St",
        },
    )
    assert create_restaurant.status_code == 201, create_restaurant.text
    restaurant = create_restaurant.json()

    create_rating = client.post(
        f"/api/v1/restaurants/{restaurant['id']}/rating",
        json={
            "rating": 4,
            "visited": True,
            "would_return": True,
            "notes": "Great coffee and quiet seating.",
        },
        headers=headers,
    )
    assert create_rating.status_code == 201, create_rating.text
    first = create_rating.json()
    assert first["restaurant_id"] == restaurant["id"]
    assert first["rating"] == 4
    assert first["would_return"] is True

    update_rating = client.post(
        f"/api/v1/restaurants/{restaurant['id']}/rating",
        json={
            "rating": 5,
            "visited": True,
            "would_return": True,
            "notes": "Updated rating after second visit",
        },
        headers=headers,
    )
    assert update_rating.status_code == 200, update_rating.text
    updated = update_rating.json()
    assert updated["id"] == first["id"]
    assert updated["rating"] == 5
    assert updated["notes"] == "Updated rating after second visit"

    my_ratings = client.get("/api/v1/me/restaurant-ratings", headers=headers)
    assert my_ratings.status_code == 200, my_ratings.text
    rows = my_ratings.json()
    assert len(rows) == 1
    assert rows[0]["restaurant"]["id"] == restaurant["id"]
    assert rows[0]["restaurant"]["name"] == restaurant["name"]
    assert rows[0]["rating"] == 5


def test_restaurant_rating_requires_existing_restaurant(client):
    suffix = uuid4().hex[:8]
    _user, headers = _register_user(client, suffix=f"missing-restaurant-{suffix}")

    response = client.post(
        "/api/v1/restaurants/999999/rating",
        json={"rating": 3, "visited": True},
        headers=headers,
    )
    assert response.status_code == 404
