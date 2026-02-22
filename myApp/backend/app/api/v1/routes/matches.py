from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_db_user, get_db
from app.crud import social as crud_social
from app.models.user import User
from app.schemas.social import MatchRead, MatchSignals, UserPublicRead

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_db_user),
    db: Session = Depends(get_db),
) -> list[MatchRead]:
    excluded_ids = {current_user.id}
    excluded_ids |= crud_social.get_friend_ids(db, current_user.id)
    excluded_ids |= crud_social.get_related_pending_request_user_ids(db, current_user.id)

    candidates = crud_social.list_discoverable_users_excluding(db, excluded_ids, limit=limit, offset=offset)
    user_ids = [current_user.id, *[candidate.id for candidate in candidates]]
    hobby_map = crud_social.get_user_hobby_codes_map(db, user_ids)

    current_hobbies = set(hobby_map.get(current_user.id, []))
    current_neighborhood = (current_user.neighborhood or "").strip().lower()
    results: list[MatchRead] = []

    for candidate in candidates:
        candidate_hobbies = hobby_map.get(candidate.id, [])
        overlap_hobbies = sorted(current_hobbies.intersection(candidate_hobbies))
        same_neighborhood = bool(
            current_neighborhood
            and candidate.neighborhood
            and current_neighborhood == candidate.neighborhood.strip().lower()
        )

        score = (1 if same_neighborhood else 0) + len(overlap_hobbies)
        if score <= 0:
            continue

        results.append(
            MatchRead(
                user=UserPublicRead.model_validate(candidate).model_copy(
                    update={"hobbies": list(candidate_hobbies)}
                ),
                score=score,
                signals=MatchSignals(
                    same_neighborhood=same_neighborhood,
                    hobby_overlap_count=len(overlap_hobbies),
                    overlap_hobbies=overlap_hobbies,
                ),
            )
        )

    results.sort(
        key=lambda item: (
            item.score,
            item.signals.hobby_overlap_count,
            1 if item.signals.same_neighborhood else 0,
            item.user.id.hex,
        ),
        reverse=True,
    )
    return results
