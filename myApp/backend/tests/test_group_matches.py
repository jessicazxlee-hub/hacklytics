from uuid import UUID, uuid4

from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue


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
    user = response.json()
    token = create_access_token(subject=firebase_uid)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _seed_group(
    test_engine,
    *,
    members: list[tuple[str, str]],
    group_status: str = "forming",
    group_match_mode: str = "in_person",
    with_venue: bool = True,
    chat_room_key: str | None = None,
) -> str:
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as db:
        group = GroupMatch(
            status=group_status,
            group_match_mode=group_match_mode,
            created_source="system",
            chat_room_key=chat_room_key,
        )
        db.add(group)
        db.flush()

        if with_venue:
            db.add(
                GroupMatchVenue(
                    group_match_id=group.id,
                    venue_kind="restaurant",
                    source="manual",
                    name_snapshot="Seed Venue",
                )
            )

        for idx, (user_id, status) in enumerate(members, start=1):
            kwargs = {
                "group_match_id": group.id,
                "user_id": UUID(user_id),
                "status": status,
                "slot_number": idx,
            }
            if status == "accepted":
                member = GroupMatchMember(**kwargs)
                member.joined_at = member.invited_at
            else:
                member = GroupMatchMember(**kwargs)
            db.add(member)

        db.commit()
        return str(group.id)


def test_list_and_accept_group_match_invite_promotes_confirmed(client, test_engine):
    suffix = uuid4().hex[:8]
    u1, h1 = _register_user(client, suffix=f"gm-a-{suffix}")
    u2, h2 = _register_user(client, suffix=f"gm-b-{suffix}")
    u3, h3 = _register_user(client, suffix=f"gm-c-{suffix}")
    u4, h4 = _register_user(client, suffix=f"gm-d-{suffix}")

    group_id = _seed_group(
        test_engine,
        members=[
            (u1["id"], "accepted"),
            (u2["id"], "accepted"),
            (u3["id"], "accepted"),
            (u4["id"], "invited"),
        ],
        group_status="forming",
        with_venue=True,
    )

    list_response = client.get("/api/v1/group-matches", headers=h4)
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    assert len(body) == 1
    assert body[0]["id"] == group_id
    assert body[0]["my_member_status"] == "invited"
    assert body[0]["status"] == "forming"

    accept_response = client.post(f"/api/v1/group-matches/{group_id}/accept", headers=h4)
    assert accept_response.status_code == 200, accept_response.text
    accepted = accept_response.json()
    assert accepted["id"] == group_id
    assert accepted["my_member_status"] == "accepted"
    assert accepted["status"] == "confirmed"
    assert accepted["member_counts"]["accepted"] == 4
    assert accepted["chat_room_key"] is not None

    detail_response = client.get(f"/api/v1/group-matches/{group_id}", headers=h4)
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "confirmed"


def test_decline_and_leave_group_match_membership_flows(client, test_engine):
    suffix = uuid4().hex[:8]
    a, ha = _register_user(client, suffix=f"decl-a-{suffix}")
    b, hb = _register_user(client, suffix=f"decl-b-{suffix}")
    c, hc = _register_user(client, suffix=f"decl-c-{suffix}")
    d, hd = _register_user(client, suffix=f"decl-d-{suffix}")
    outsider, ho = _register_user(client, suffix=f"decl-o-{suffix}")

    decline_group_id = _seed_group(
        test_engine,
        members=[
            (a["id"], "accepted"),
            (b["id"], "invited"),
        ],
        group_status="forming",
        with_venue=True,
    )

    outsider_decline = client.post(f"/api/v1/group-matches/{decline_group_id}/decline", headers=ho)
    assert outsider_decline.status_code == 404

    decline_response = client.post(f"/api/v1/group-matches/{decline_group_id}/decline", headers=hb)
    assert decline_response.status_code == 200, decline_response.text
    declined = decline_response.json()
    assert declined["my_member_status"] == "declined"
    assert declined["status"] == "forming"
    assert declined["member_counts"]["declined"] == 1

    active_list = client.get("/api/v1/group-matches", headers=hb)
    assert active_list.status_code == 200
    assert active_list.json() == []

    inactive_list = client.get("/api/v1/group-matches?include_inactive_memberships=true", headers=hb)
    assert inactive_list.status_code == 200
    assert len(inactive_list.json()) == 1
    assert inactive_list.json()[0]["id"] == decline_group_id
    assert inactive_list.json()[0]["my_member_status"] == "declined"

    leave_group_id = _seed_group(
        test_engine,
        members=[
            (a["id"], "accepted"),
            (c["id"], "accepted"),
            (d["id"], "accepted"),
            (b["id"], "accepted"),
        ],
        group_status="confirmed",
        with_venue=True,
        chat_room_key=f"group-{uuid4().hex[:8]}",
    )

    leave_response = client.post(f"/api/v1/group-matches/{leave_group_id}/leave", headers=hb)
    assert leave_response.status_code == 200, leave_response.text
    left = leave_response.json()
    assert left["my_member_status"] == "left"
    assert left["member_counts"]["accepted"] == 3
    # Preserve the invariant that confirmed means 4 accepted members.
    assert left["status"] == "forming"

    # Can't leave again once not accepted.
    leave_again = client.post(f"/api/v1/group-matches/{leave_group_id}/leave", headers=hb)
    assert leave_again.status_code == 409
