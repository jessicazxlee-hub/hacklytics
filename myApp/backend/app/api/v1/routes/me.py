from fastapi import APIRouter, Depends

from app.core.deps import get_current_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("")
def read_me(current_user: dict = Depends(get_current_user)) -> dict:
    return {"user": current_user}


@router.get("/profile")
def read_profile(current_user: dict = Depends(get_current_user)) -> dict:
    return {"profile": current_user}
