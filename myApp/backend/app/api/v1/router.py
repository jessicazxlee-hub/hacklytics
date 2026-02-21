from fastapi import APIRouter

from app.api.v1.routes.admin_hobbies import router as admin_hobbies_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.me import router as me_router
from app.api.v1.routes.restaurants import router as restaurants_router

router = APIRouter()
router.include_router(admin_hobbies_router)
router.include_router(auth_router)
router.include_router(me_router)
router.include_router(restaurants_router)
