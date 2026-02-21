from uuid import uuid4

from app.core.config import settings
from app.core.security import create_access_token


def test_me_profile_supports_display_name_and_hobbies(client):
    unique_suffix = uuid4().hex[:8]
    register_payload = {
        "email": f"me-{unique_suffix}@example.com",
        "password": "password123",
        "firebase_uid": f"firebase-me-{unique_suffix}",
        "neighborhood": "Downtown",
    }
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    admin_headers = {"X-Admin-Key": settings.admin_api_key}
    hobby_code = f"coding_{unique_suffix}"
    hobby_payload = {"code": hobby_code, "label": "Coding", "is_active": True}
    hobby_response = client.post("/api/v1/admin/hobbies", json=hobby_payload, headers=admin_headers)
    assert hobby_response.status_code == 201

    token = create_access_token(subject=register_payload["firebase_uid"])
    auth_headers = {"Authorization": f"Bearer {token}"}

    read_response = client.get("/api/v1/me/profile", headers=auth_headers)
    assert read_response.status_code == 200
    assert read_response.json()["display_name"] is None
    assert read_response.json()["hobbies"] == []

    update_payload = {
        "display_name": f"proximity_{unique_suffix}",
        "hobbies": [hobby_code],
    }
    update_response = client.patch("/api/v1/me/profile", json=update_payload, headers=auth_headers)
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == f"proximity_{unique_suffix}"
    assert update_response.json()["hobbies"] == [hobby_code]
