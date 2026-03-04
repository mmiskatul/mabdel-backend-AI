from fastapi import APIRouter

from app.api.v1.routers.permission_router import router as permission_router
from app.api.v1.routers.user_router import router as user_router

api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(permission_router)
