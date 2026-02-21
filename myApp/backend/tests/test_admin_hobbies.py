from uuid import uuid4

from app.core.config import settings


def test_admin_hobbies_requires_key(client):
    response = client.get("/api/v1/admin/hobbies")
    assert response.status_code == 403


def test_admin_hobbies_create_and_seed(client):
    headers = {"X-Admin-Key": settings.admin_api_key}

    unique_code = f"board_games_{uuid4().hex[:8]}"
    create_payload = {"code": unique_code, "label": "Board Games", "is_active": True}
    create_response = client.post("/api/v1/admin/hobbies", json=create_payload, headers=headers)
    assert create_response.status_code == 201
    assert create_response.json()["code"] == unique_code

    seed_response = client.post("/api/v1/admin/hobbies/seed", headers=headers)
    assert seed_response.status_code == 200
    assert seed_response.json()["total_input"] >= 1
