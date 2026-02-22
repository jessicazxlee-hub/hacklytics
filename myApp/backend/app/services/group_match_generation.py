from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.crud import social as crud_social
from app.models.group_match import GroupMatch, GroupMatchMember, GroupMatchVenue
from app.models.user import User
from app.schemas.group_match_generation import (
    GroupMatchGenerateRequest,
    GroupMatchGenerateResponse,
    GroupMatchGeneratedGroupSummary,
    GroupMatchGenerateScoreSummary,
)

ACTIVE_GROUP_STATUSES = ("forming", "confirmed", "scheduled")
ACTIVE_MEMBER_STATUSES = ("invited", "accepted")


@dataclass
class ProposedGroup:
    member_ids: list[UUID]
    venue_name: str | None
    status: str
    mode: str
    score_summary: GroupMatchGenerateScoreSummary
    group_match_id: UUID | None = None


def _normalized_neighborhood(value: str | None) -> str:
    return (value or "").strip().lower()


def _pair_overlap_count(hobbies_a: set[str], hobbies_b: set[str]) -> int:
    return len(hobbies_a.intersection(hobbies_b))


def _candidate_score(
    candidate: User,
    current_group: list[User],
    *,
    hobby_map: dict[UUID, list[str]],
    same_neighborhood_preferred: bool,
) -> tuple[int, int, int]:
    candidate_hobbies = set(hobby_map.get(candidate.id, []))
    pair_overlap_total = 0
    same_neighborhood_pairs = 0
    for member in current_group:
        member_hobbies = set(hobby_map.get(member.id, []))
        pair_overlap_total += _pair_overlap_count(candidate_hobbies, member_hobbies)
        if same_neighborhood_preferred and _normalized_neighborhood(candidate.neighborhood) and (
            _normalized_neighborhood(candidate.neighborhood) == _normalized_neighborhood(member.neighborhood)
        ):
            same_neighborhood_pairs += 1

    weighted_score = pair_overlap_total + (2 * same_neighborhood_pairs if same_neighborhood_preferred else 0)
    # Return tiebreakers explicitly for stable sorting.
    return weighted_score, pair_overlap_total, same_neighborhood_pairs


def _group_score_summary(
    users: list[User],
    *,
    hobby_map: dict[UUID, list[str]],
) -> GroupMatchGenerateScoreSummary:
    overlaps: list[int] = []
    same_neighborhood_pairs = 0
    for left, right in combinations(users, 2):
        left_hobbies = set(hobby_map.get(left.id, []))
        right_hobbies = set(hobby_map.get(right.id, []))
        overlaps.append(_pair_overlap_count(left_hobbies, right_hobbies))
        if _normalized_neighborhood(left.neighborhood) and (
            _normalized_neighborhood(left.neighborhood) == _normalized_neighborhood(right.neighborhood)
        ):
            same_neighborhood_pairs += 1

    avg_overlap = (sum(overlaps) / len(overlaps)) if overlaps else 0.0
    return GroupMatchGenerateScoreSummary(
        avg_pair_hobby_overlap=round(avg_overlap, 3),
        same_neighborhood_pairs=same_neighborhood_pairs,
    )


def _active_grouped_user_ids(db: Session) -> set[UUID]:
    stmt = (
        select(GroupMatchMember.user_id)
        .join(GroupMatch, GroupMatch.id == GroupMatchMember.group_match_id)
        .where(
            GroupMatch.status.in_(ACTIVE_GROUP_STATUSES),
            GroupMatchMember.status.in_(ACTIVE_MEMBER_STATUSES),
        )
    )
    return set(db.scalars(stmt).all())


def _eligible_users_for_mode(db: Session, mode: str) -> list[User]:
    stmt = select(User).where(User.discoverable.is_(True))
    if mode == "in_person":
        stmt = stmt.where(User.open_to_meetups.is_(True))
    elif mode == "chat_only":
        stmt = stmt.where(User.open_to_meetups.is_(False))
    stmt = stmt.order_by(User.created_at.asc(), User.id.asc())
    return list(db.scalars(stmt).all())


def _choose_venue_name(group_users: list[User], *, mode: str) -> str | None:
    if mode == "chat_only":
        return None
    neighborhoods = [u.neighborhood for u in group_users if (u.neighborhood or "").strip()]
    if neighborhoods:
        return f"{neighborhoods[0]} Meetup Spot"
    return "Proximity Meetup Spot"


def _propose_groups(
    users: list[User],
    *,
    request: GroupMatchGenerateRequest,
    hobby_map: dict[UUID, list[str]],
) -> tuple[list[ProposedGroup], int]:
    target_size = request.target_group_size
    remaining = list(users)
    proposed: list[ProposedGroup] = []

    while remaining and len(proposed) < request.max_groups:
        anchor = remaining[0]
        group_members = [anchor]
        candidate_pool = remaining[1:]

        while len(group_members) < target_size and candidate_pool:
            candidate_pool.sort(
                key=lambda c: (
                    *_candidate_score(
                        c,
                        group_members,
                        hobby_map=hobby_map,
                        same_neighborhood_preferred=request.same_neighborhood_preferred,
                    ),
                    str(c.id),
                ),
                reverse=True,
            )
            best = candidate_pool.pop(0)
            group_members.append(best)

        if len(group_members) < target_size:
            # Not enough users left to form another full group.
            break

        summary = _group_score_summary(group_members, hobby_map=hobby_map)
        proposed.append(
            ProposedGroup(
                member_ids=[u.id for u in group_members],
                venue_name=_choose_venue_name(group_members, mode=request.mode),
                status="forming",
                mode=request.mode,
                score_summary=summary,
            )
        )
        assigned_ids = {u.id for u in group_members}
        remaining = [u for u in remaining if u.id not in assigned_ids]

    return proposed, len(remaining)


def _persist_proposed_groups(
    db: Session,
    *,
    proposed: list[ProposedGroup],
) -> None:
    for item in proposed:
        group = GroupMatch(
            status=item.status,
            group_match_mode=item.mode,
            created_source="system",
        )
        db.add(group)
        db.flush()

        for idx, user_id in enumerate(item.member_ids, start=1):
            db.add(
                GroupMatchMember(
                    group_match_id=group.id,
                    user_id=user_id,
                    status="invited",
                    slot_number=idx,
                )
            )

        if item.venue_name is not None:
            db.add(
                GroupMatchVenue(
                    group_match_id=group.id,
                    venue_kind="restaurant" if item.mode == "in_person" else "custom",
                    source="manual",
                    name_snapshot=item.venue_name,
                )
            )

        item.group_match_id = group.id

    db.commit()


def generate_group_matches(db: Session, request: GroupMatchGenerateRequest) -> GroupMatchGenerateResponse:
    if request.target_group_size != 4:
        # Product constraint for now; keep parameter for future evolution.
        raise ValueError("Only target_group_size=4 is supported right now")

    all_discoverable_in_mode = _eligible_users_for_mode(db, request.mode)
    active_group_user_ids = _active_grouped_user_ids(db)

    eligible_pool = [user for user in all_discoverable_in_mode if user.id not in active_group_user_ids]
    hobby_map = crud_social.get_user_hobby_codes_map(db, [u.id for u in eligible_pool])

    proposed, unassigned_from_pool = _propose_groups(
        eligible_pool,
        request=request,
        hobby_map=hobby_map,
    )

    if not request.dry_run and proposed:
        _persist_proposed_groups(db, proposed=proposed)

    skip_reasons: Counter[str] = Counter()
    if active_group_user_ids:
        # Count only active-group users that otherwise match the mode/discoverable filters.
        skip_reasons["already_in_active_group"] = sum(1 for u in all_discoverable_in_mode if u.id in active_group_user_ids)

    if unassigned_from_pool:
        if len(proposed) >= request.max_groups:
            skip_reasons["max_groups_cap_reached"] += unassigned_from_pool
        else:
            skip_reasons["insufficient_candidates"] += unassigned_from_pool

    groups = [
        GroupMatchGeneratedGroupSummary(
            group_match_id=item.group_match_id,
            mode=item.mode,  # type: ignore[arg-type]
            status=item.status,
            member_ids=item.member_ids,
            venue_name=item.venue_name,
            score_summary=item.score_summary,
        )
        for item in proposed
    ]

    return GroupMatchGenerateResponse(
        dry_run=request.dry_run,
        created_groups=0 if request.dry_run else len(proposed),
        skipped_users=sum(skip_reasons.values()),
        skip_reasons=dict(skip_reasons),
        groups=groups,
    )
