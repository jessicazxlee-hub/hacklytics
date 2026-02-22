from uuid import uuid4

from app.core.config import settings
from app.core.security import create_access_token


def _register_user(
    client,
    *,
    suffix: str,
    neighborhood: str = "Downtown",
    open_to_meetups: bool = True,
    discoverable: bool = True,
):
    firebase_uid = f"firebase-{suffix}"
    payload = {
        "email": f"{suffix}@example.com",
        "password": "password123",
        "firebase_uid": firebase_uid,
        "neighborhood": neighborhood,
        "open_to_meetups": open_to_meetups,
        "discoverable": discoverable,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    user = response.json()
    token = create_access_token(subject=firebase_uid)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _admin_headers() -> dict[str, str]:
    return {"X-Admin-Key": settings.admin_api_key}


def test_admin_group_match_generation_dry_run_and_create(client):
    suffix = uuid4().hex[:8]
    users = []
    for idx in range(8):
        user, _headers = _register_user(
            client,
            suffix=f"gen-{idx}-{suffix}",
            neighborhood="Downtown" if idx < 4 else "Midtown",
            open_to_meetups=True,
        )
        users.append(user)

    payload = {
        "mode": "in_person",
        "max_groups": 2,
        "target_group_size": 4,
        "same_neighborhood_preferred": True,
        "dry_run": True,
    }
    dry_run = client.post("/api/v1/admin/group-matches/generate", json=payload, headers=_admin_headers())
    assert dry_run.status_code == 200, dry_run.text
    body = dry_run.json()
    assert body["dry_run"] is True
    assert body["created_groups"] == 0
    assert len(body["groups"]) == 2
    assert all(group["group_match_id"] is None for group in body["groups"])
    assert all(group["status"] == "forming" for group in body["groups"])
    assert all(len(group["member_ids"]) == 4 for group in body["groups"])

    payload["dry_run"] = False
    created = client.post("/api/v1/admin/group-matches/generate", json=payload, headers=_admin_headers())
    assert created.status_code == 200, created.text
    created_body = created.json()
    assert created_body["dry_run"] is False
    assert created_body["created_groups"] == 2
    assert len(created_body["groups"]) == 2
    assert all(group["group_match_id"] is not None for group in created_body["groups"])

    # Rerun should skip because users are already in active generated groups.
    rerun = client.post("/api/v1/admin/group-matches/generate", json=payload, headers=_admin_headers())
    assert rerun.status_code == 200, rerun.text
    rerun_body = rerun.json()
    assert rerun_body["created_groups"] == 0
    assert rerun_body["skip_reasons"].get("already_in_active_group", 0) >= 8


def test_admin_group_match_generation_chat_only_filters_open_to_meetups(client):
    suffix = uuid4().hex[:8]
    for idx in range(4):
        _register_user(
            client,
            suffix=f"chatonly-off-{idx}-{suffix}",
            neighborhood="Uptown",
            open_to_meetups=False,
        )
    for idx in range(4):
        _register_user(
            client,
            suffix=f"chatonly-on-{idx}-{suffix}",
            neighborhood="Uptown",
            open_to_meetups=True,
        )

    response = client.post(
        "/api/v1/admin/group-matches/generate",
        json={
            "mode": "chat_only",
            "max_groups": 2,
            "target_group_size": 4,
            "dry_run": False,
        },
        headers=_admin_headers(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created_groups"] == 1
    assert len(body["groups"]) == 1
    group = body["groups"][0]
    assert group["mode"] == "chat_only"
    assert group["venue_name"] is None
