from uuid import uuid4

from app.core.config import settings
from app.core.security import create_access_token


def _register_user(client, *, suffix: str, neighborhood: str | None = None):
    firebase_uid = f"firebase-{suffix}"
    payload = {
        "email": f"{suffix}@example.com",
        "password": "password123",
        "firebase_uid": firebase_uid,
        "neighborhood": neighborhood,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user = response.json()
    token = create_access_token(subject=firebase_uid)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _create_hobby(client, code: str, label: str):
    admin_headers = {"X-Admin-Key": settings.admin_api_key}
    response = client.post(
        "/api/v1/admin/hobbies",
        json={"code": code, "label": label, "is_active": True},
        headers=admin_headers,
    )
    assert response.status_code == 201


def _patch_me_profile(client, headers: dict[str, str], payload: dict):
    response = client.patch("/api/v1/me/profile", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_friend_request_accept_and_list_friends(client):
    suffix = uuid4().hex[:8]
    requester, requester_headers = _register_user(client, suffix=f"requester-{suffix}", neighborhood="Downtown")
    addressee, addressee_headers = _register_user(client, suffix=f"addressee-{suffix}", neighborhood="Downtown")

    create_response = client.post(f"/api/v1/friends/requests/{addressee['id']}", headers=requester_headers)
    assert create_response.status_code == 201
    create_body = create_response.json()
    assert create_body["created"] is True
    assert create_body["status"] == "pending"

    duplicate_response = client.post(f"/api/v1/friends/requests/{addressee['id']}", headers=requester_headers)
    assert duplicate_response.status_code == 200
    duplicate_body = duplicate_response.json()
    assert duplicate_body["created"] is False
    assert duplicate_body["id"] == create_body["id"]

    # Only addressee can accept.
    forbidden_accept = client.post(f"/api/v1/friends/requests/{create_body['id']}/accept", headers=requester_headers)
    assert forbidden_accept.status_code == 403

    accept_response = client.post(f"/api/v1/friends/requests/{create_body['id']}/accept", headers=addressee_headers)
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "accepted"

    requester_friends = client.get("/api/v1/friends", headers=requester_headers)
    assert requester_friends.status_code == 200
    assert len(requester_friends.json()) == 1
    assert requester_friends.json()[0]["user"]["id"] == addressee["id"]

    addressee_friends = client.get("/api/v1/friends", headers=addressee_headers)
    assert addressee_friends.status_code == 200
    assert len(addressee_friends.json()) == 1
    assert addressee_friends.json()[0]["user"]["id"] == requester["id"]


def test_matches_scores_and_excludes_pending_and_friends(client):
    suffix = uuid4().hex[:8]
    current_user, current_headers = _register_user(client, suffix=f"me-{suffix}", neighborhood="Downtown")
    pending_user, pending_headers = _register_user(client, suffix=f"pending-{suffix}", neighborhood="Downtown")
    friend_user, friend_headers = _register_user(client, suffix=f"friend-{suffix}", neighborhood="Downtown")
    top_match_user, top_match_headers = _register_user(client, suffix=f"top-{suffix}", neighborhood="Downtown")
    low_match_user, low_match_headers = _register_user(client, suffix=f"low-{suffix}", neighborhood="Uptown")
    hidden_user, hidden_headers = _register_user(client, suffix=f"hidden-{suffix}", neighborhood="Downtown")

    coffee = f"coffee_{suffix}"
    hiking = f"hiking_{suffix}"
    movies = f"movies_{suffix}"
    _create_hobby(client, coffee, "Coffee")
    _create_hobby(client, hiking, "Hiking")
    _create_hobby(client, movies, "Movies")

    _patch_me_profile(client, current_headers, {"display_name": "me", "hobbies": [coffee, hiking]})
    _patch_me_profile(client, pending_headers, {"display_name": "pending", "hobbies": [coffee]})
    _patch_me_profile(client, friend_headers, {"display_name": "friend", "hobbies": [hiking]})
    _patch_me_profile(client, top_match_headers, {"display_name": "top", "hobbies": [coffee]})
    _patch_me_profile(client, low_match_headers, {"display_name": "low", "hobbies": [hiking]})
    _patch_me_profile(
        client,
        hidden_headers,
        {"display_name": "hidden", "hobbies": [coffee], "discoverable": False},
    )

    # Create one pending request (should exclude pending_user from matches)
    pending_request = client.post(f"/api/v1/friends/requests/{pending_user['id']}", headers=current_headers)
    assert pending_request.status_code == 201

    # Create and accept one friendship (should exclude friend_user from matches)
    friend_request = client.post(f"/api/v1/friends/requests/{friend_user['id']}", headers=current_headers)
    assert friend_request.status_code == 201
    accept_friend = client.post(
        f"/api/v1/friends/requests/{friend_request.json()['id']}/accept",
        headers=friend_headers,
    )
    assert accept_friend.status_code == 200

    matches_response = client.get("/api/v1/matches", headers=current_headers)
    assert matches_response.status_code == 200
    matches = matches_response.json()

    returned_ids = [match["user"]["id"] for match in matches]
    assert top_match_user["id"] in returned_ids
    assert low_match_user["id"] in returned_ids
    assert pending_user["id"] not in returned_ids
    assert friend_user["id"] not in returned_ids
    assert hidden_user["id"] not in returned_ids
    assert current_user["id"] not in returned_ids

    top_entry = next(match for match in matches if match["user"]["id"] == top_match_user["id"])
    low_entry = next(match for match in matches if match["user"]["id"] == low_match_user["id"])

    assert top_entry["signals"]["same_neighborhood"] is True
    assert top_entry["signals"]["hobby_overlap_count"] == 1
    assert top_entry["score"] == 2

    assert low_entry["signals"]["same_neighborhood"] is False
    assert low_entry["signals"]["hobby_overlap_count"] == 1
    assert low_entry["score"] == 1

    assert matches[0]["user"]["id"] == top_match_user["id"]


def test_incoming_outgoing_and_decline_cancel_flows(client):
    suffix = uuid4().hex[:8]
    sender, sender_headers = _register_user(client, suffix=f"sender-{suffix}", neighborhood="Downtown")
    receiver, receiver_headers = _register_user(client, suffix=f"receiver-{suffix}", neighborhood="Downtown")
    other, other_headers = _register_user(client, suffix=f"other-{suffix}", neighborhood="Downtown")

    create_response = client.post(f"/api/v1/friends/requests/{receiver['id']}", headers=sender_headers)
    assert create_response.status_code == 201
    request_id = create_response.json()["id"]

    outgoing = client.get("/api/v1/friends/requests/outgoing", headers=sender_headers)
    assert outgoing.status_code == 200
    assert len(outgoing.json()) == 1
    assert outgoing.json()[0]["request"]["id"] == request_id
    assert outgoing.json()[0]["user"]["id"] == receiver["id"]

    incoming = client.get("/api/v1/friends/requests/incoming", headers=receiver_headers)
    assert incoming.status_code == 200
    assert len(incoming.json()) == 1
    assert incoming.json()[0]["request"]["id"] == request_id
    assert incoming.json()[0]["user"]["id"] == sender["id"]

    # Wrong actor cannot cancel/decline.
    forbidden_cancel = client.post(f"/api/v1/friends/requests/{request_id}/cancel", headers=receiver_headers)
    assert forbidden_cancel.status_code == 403
    forbidden_decline = client.post(f"/api/v1/friends/requests/{request_id}/decline", headers=sender_headers)
    assert forbidden_decline.status_code == 403

    cancelled = client.post(f"/api/v1/friends/requests/{request_id}/cancel", headers=sender_headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    outgoing_after_cancel = client.get("/api/v1/friends/requests/outgoing", headers=sender_headers)
    incoming_after_cancel = client.get("/api/v1/friends/requests/incoming", headers=receiver_headers)
    assert outgoing_after_cancel.status_code == 200
    assert incoming_after_cancel.status_code == 200
    assert outgoing_after_cancel.json() == []
    assert incoming_after_cancel.json() == []

    # Re-send to same user should work by reopening the prior directional row.
    resend_response = client.post(f"/api/v1/friends/requests/{receiver['id']}", headers=sender_headers)
    assert resend_response.status_code == 201
    assert resend_response.json()["created"] is True
    assert resend_response.json()["status"] == "pending"
    assert resend_response.json()["id"] == request_id

    declined = client.post(f"/api/v1/friends/requests/{request_id}/decline", headers=receiver_headers)
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    # A third user should not see unrelated requests.
    other_incoming = client.get("/api/v1/friends/requests/incoming", headers=other_headers)
    other_outgoing = client.get("/api/v1/friends/requests/outgoing", headers=other_headers)
    assert other_incoming.status_code == 200
    assert other_outgoing.status_code == 200
    assert other_incoming.json() == []
    assert other_outgoing.json() == []
