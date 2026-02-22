from uuid import UUID, uuid4

from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.models.group_chat import GroupChatMessage
from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue


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
    user = response.json()
    token = create_access_token(subject=firebase_uid)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _seed_confirmed_group_chat(test_engine, *, member_user_ids: list[str]) -> str:
    member_ids = [UUID(user_id) for user_id in member_user_ids]
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as db:
        group = GroupMatch(
            status="confirmed",
            group_match_mode="in_person",
            created_source="system",
            chat_room_key=f"group-{uuid4().hex[:12]}",
        )
        db.add(group)
        db.flush()

        db.add(
            GroupMatchVenue(
                group_match_id=group.id,
                venue_kind="restaurant",
                source="manual",
                name_snapshot="Test Venue",
            )
        )

        for idx, user_id in enumerate(member_ids, start=1):
            db.add(
                GroupMatchMember(
                    group_match_id=group.id,
                    user_id=user_id,
                    status="accepted",
                    slot_number=idx,
                )
            )

        db.flush()
        db.add(
            GroupChatMessage(
                group_match_id=group.id,
                sender_user_id=member_ids[0],
                body="hello group",
            )
        )
        db.commit()
        return str(group.id)


def test_group_chats_list_and_messages_for_members(client, test_engine):
    suffix = uuid4().hex[:8]
    user_a, headers_a = _register_user(client, suffix=f"a-{suffix}")
    user_b, headers_b = _register_user(client, suffix=f"b-{suffix}")
    _outsider, outsider_headers = _register_user(client, suffix=f"o-{suffix}")

    group_id = _seed_confirmed_group_chat(test_engine, member_user_ids=[user_a["id"], user_b["id"]])

    list_response = client.get("/api/v1/chats", headers=headers_a)
    assert list_response.status_code == 200, list_response.text
    chats = list_response.json()
    assert len(chats) == 1
    assert chats[0]["id"] == group_id
    assert chats[0]["member_count"] == 2
    assert chats[0]["venue_name"] == "Test Venue"
    assert chats[0]["last_message"]["body_preview"] == "hello group"

    messages_response = client.get(f"/api/v1/chats/{group_id}/messages", headers=headers_b)
    assert messages_response.status_code == 200, messages_response.text
    messages = messages_response.json()
    assert len(messages) == 1
    assert messages[0]["body"] == "hello group"
    assert messages[0]["sender"]["id"] == user_a["id"]

    send_response = client.post(
        f"/api/v1/chats/{group_id}/messages",
        json={"body": "  second message  "},
        headers=headers_b,
    )
    assert send_response.status_code == 201, send_response.text
    sent = send_response.json()
    assert sent["body"] == "second message"
    assert sent["sender"]["id"] == user_b["id"]

    outsider_read = client.get(f"/api/v1/chats/{group_id}/messages", headers=outsider_headers)
    assert outsider_read.status_code == 404


def test_group_chat_disallows_forming_groups(client, test_engine):
    suffix = uuid4().hex[:8]
    user, headers = _register_user(client, suffix=f"user-{suffix}")

    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    with Session() as db:
        group = GroupMatch(
            status="forming",
            group_match_mode="in_person",
            created_source="system",
        )
        db.add(group)
        db.flush()
        db.add(
            GroupMatchMember(
                group_match_id=group.id,
                user_id=UUID(user["id"]),
                status="accepted",
                slot_number=1,
            )
        )
        db.commit()
        group_id = str(group.id)

    response = client.get(f"/api/v1/chats/{group_id}/messages", headers=headers)
    assert response.status_code == 404
