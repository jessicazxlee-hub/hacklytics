from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin_key
from app.schemas.group_match_generation import GroupMatchGenerateRequest, GroupMatchGenerateResponse
from app.services.group_match_generation import generate_group_matches

router = APIRouter(
    prefix="/admin/group-matches",
    tags=["admin-group-matches"],
    dependencies=[Depends(require_admin_key)],
)


@router.post("/generate", response_model=GroupMatchGenerateResponse)
def generate_group_matches_admin(
    payload: GroupMatchGenerateRequest,
    db: Session = Depends(get_db),
) -> GroupMatchGenerateResponse:
    try:
        return generate_group_matches(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
