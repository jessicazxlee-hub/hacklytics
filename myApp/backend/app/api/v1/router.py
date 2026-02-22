from fastapi import APIRouter

from app.api.v1.routes.admin_embeddings import router as admin_embeddings_router
from app.api.v1.routes.admin_hobbies import router as admin_hobbies_router
from app.api.v1.routes.admin_group_matches import router as admin_group_matches_router
from app.api.v1.routes.admin_vector import router as admin_vector_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.chats import router as chats_router
from app.api.v1.routes.friends import router as friends_router
from app.api.v1.routes.group_matches import router as group_matches_router
from app.api.v1.routes.hobbies import router as hobbies_router
from app.api.v1.routes.matches import router as matches_router
from app.api.v1.routes.me import router as me_router
from app.api.v1.routes.restaurants import router as restaurants_router

router = APIRouter()
router.include_router(admin_embeddings_router)
router.include_router(admin_hobbies_router)
router.include_router(admin_group_matches_router)
router.include_router(admin_vector_router)
router.include_router(auth_router)
router.include_router(chats_router)
router.include_router(friends_router)
router.include_router(group_matches_router)
router.include_router(hobbies_router)
router.include_router(matches_router)
router.include_router(me_router)
router.include_router(restaurants_router)
