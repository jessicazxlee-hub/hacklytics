from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.group_chat import GroupChatMessage
from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue
from app.models.user import User


@dataclass(frozen=True)
class DemoCompanionSpec:
    key: str
    display_name: str
    neighborhood: str
    open_to_meetups: bool


DEMO_COMPANIONS: tuple[DemoCompanionSpec, ...] = (
    DemoCompanionSpec("ava", "Ava", "Downtown", True),
    DemoCompanionSpec("ben", "Ben", "Downtown", True),
    DemoCompanionSpec("cleo", "Cleo", "Midtown", True),
    DemoCompanionSpec("diego", "Diego", "Downtown", True),
    DemoCompanionSpec("elena", "Elena", "Uptown", False),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed demo group matches and group chat messages for a target user (dev only by default)."
    )
    parser.add_argument("--email", required=True, help="Existing Postgres user email to attach demo groups to")
    parser.add_argument(
        "--allow-non-dev",
        action="store_true",
        help="Allow running even when APP_ENV is not 'dev'",
    )
    return parser.parse_args()


def _demo_prefix(target_user_id: UUID) -> str:
    return f"demo-seed-{target_user_id}"


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _demo_display_name(*, base_name: str, prefix: str) -> str:
    # Keep demo companion names unique across repeated runs/targets while staying human-readable.
    suffix = prefix.replace("demo-seed-", "")[:6]
    return f"{base_name}-{suffix}"


def _get_target_user(db, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def _get_or_create_demo_user(db, *, spec: DemoCompanionSpec, prefix: str) -> User:
    email = f"{prefix}.{spec.key}@example.local"
    display_name = _demo_display_name(base_name=spec.display_name, prefix=prefix)
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        existing.display_name = display_name
        existing.neighborhood = spec.neighborhood
        existing.open_to_meetups = spec.open_to_meetups
        existing.discoverable = True
        db.add(existing)
        return existing

    user = User(
        email=email,
        display_name=display_name,
        neighborhood=spec.neighborhood,
        open_to_meetups=spec.open_to_meetups,
        discoverable=True,
        auth_provider="seed",
        email_verified=False,
        firebase_uid=None,
    )
    db.add(user)
    return user


def _delete_existing_demo_groups(db, *, prefix: str) -> int:
    stmt = select(GroupMatch).where(GroupMatch.chat_room_key.like(f"{prefix}-%"))
    groups = list(db.scalars(stmt).all())
    count = len(groups)
    for group in groups:
        db.delete(group)
    return count


def _create_group(
    db,
    *,
    key: str,
    prefix: str,
    status: str,
    mode: str,
    created_by_user_id: UUID,
    member_rows: list[tuple[User, str, int | None]],
    venue_name: str | None,
    venue_neighborhood: str | None = None,
    seed_messages: list[tuple[User, str]] | None = None,
) -> GroupMatch:
    group = GroupMatch(
        status=status,
        group_match_mode=mode,
        created_source="system",
        created_by_user_id=created_by_user_id,
        chat_room_key=f"{prefix}-{key}",
    )
    db.add(group)
    db.flush()

    if venue_name is not None:
        db.add(
            GroupMatchVenue(
                group_match_id=group.id,
                venue_kind="restaurant" if mode == "in_person" else "custom",
                source="manual",
                name_snapshot=venue_name,
                neighborhood_snapshot=venue_neighborhood,
            )
        )

    now = datetime.now(timezone.utc)
    for user, member_status, slot in member_rows:
        member = GroupMatchMember(
            group_match_id=group.id,
            user_id=user.id,
            status=member_status,
            slot_number=slot,
        )
        if member_status in {"accepted", "declined"}:
            member.responded_at = now
        if member_status == "accepted":
            member.joined_at = now
        if member_status == "left":
            member.left_at = now
        db.add(member)

    if seed_messages:
        for sender, body in seed_messages:
            db.add(
                GroupChatMessage(
                    group_match_id=group.id,
                    sender_user_id=sender.id,
                    body=body,
                )
            )

    return group


def main() -> int:
    args = parse_args()

    if settings.app_env.lower() != "dev" and not args.allow_non_dev:
        print(
            f"Refusing to run seed script because APP_ENV={settings.app_env!r}. "
            "Use --allow-non-dev to override."
        )
        return 2

    target_email = _normalize_email(args.email)

    with SessionLocal() as db:
        target = _get_target_user(db, target_email)
        if target is None:
            print(
                f"No user profile found for {target_email!r}. "
                "Log into the app and open the Profile tab first so /api/v1/me/profile bootstraps the row."
            )
            return 1

        prefix = _demo_prefix(target.id)

        removed_count = _delete_existing_demo_groups(db, prefix=prefix)

        companions = {
            spec.key: _get_or_create_demo_user(db, spec=spec, prefix=prefix)
            for spec in DEMO_COMPANIONS
        }

        db.flush()

        # Scenario 1: forming group with target invited (tests Accept/Decline in Matches)
        group_invited = _create_group(
            db,
            key="invite",
            prefix=prefix,
            status="forming",
            mode="in_person",
            created_by_user_id=target.id,
            member_rows=[
                (companions["ava"], "accepted", 1),
                (companions["ben"], "accepted", 2),
                (companions["cleo"], "accepted", 3),
                (target, "invited", 4),
            ],
            venue_name="Demo Brunch Spot",
            venue_neighborhood="Downtown",
            seed_messages=None,
        )

        # Scenario 2: confirmed group with target accepted (tests Open Chat)
        group_chat_ready = _create_group(
            db,
            key="chat",
            prefix=prefix,
            status="confirmed",
            mode="in_person",
            created_by_user_id=target.id,
            member_rows=[
                (target, "accepted", 1),
                (companions["ava"], "accepted", 2),
                (companions["diego"], "accepted", 3),
                (companions["ben"], "accepted", 4),
            ],
            venue_name="Demo Dinner Place",
            venue_neighborhood="Downtown",
            seed_messages=[
                (companions["ava"], "Hey everyone, looking forward to this."),
                (target, "Same here. I can do Friday evening."),
            ],
        )

        # Scenario 3: confirmed group with target accepted (tests Leave -> demotes to forming)
        group_leave = _create_group(
            db,
            key="leave",
            prefix=prefix,
            status="confirmed",
            mode="in_person",
            created_by_user_id=target.id,
            member_rows=[
                (target, "accepted", 1),
                (companions["cleo"], "accepted", 2),
                (companions["diego"], "accepted", 3),
                (companions["ava"], "accepted", 4),
            ],
            venue_name="Demo Coffee Meetup",
            venue_neighborhood="Midtown",
            seed_messages=[
                (companions["diego"], "I can join after 6pm."),
            ],
        )

        # Scenario 4: chat-only confirmed group (tests mode rendering + chat list)
        group_chat_only = _create_group(
            db,
            key="chatonly",
            prefix=prefix,
            status="confirmed",
            mode="chat_only",
            created_by_user_id=target.id,
            member_rows=[
                (target, "accepted", 1),
                (companions["elena"], "accepted", 2),
                (companions["ben"], "accepted", 3),
                (companions["cleo"], "accepted", 4),
            ],
            venue_name=None,
            seed_messages=[
                (companions["elena"], "Chat-only group for now, no meetup plans."),
            ],
        )

        db.commit()

        print(f"Target user: {target.email} ({target.id})")
        print(f"Removed existing demo groups: {removed_count}")
        print("Seeded demo groups:")
        for label, group in (
            ("invite", group_invited),
            ("chat", group_chat_ready),
            ("leave", group_leave),
            ("chat_only", group_chat_only),
        ):
            print(
                f"  - {label}: id={group.id} status={group.status} mode={group.group_match_mode} chat_room_key={group.chat_room_key}"
            )
        print("")
        print("Open the app and test:")
        print("  Matches tab: invited / accept / decline / leave flows")
        print("  Chats tab: confirmed groups + sample messages")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
