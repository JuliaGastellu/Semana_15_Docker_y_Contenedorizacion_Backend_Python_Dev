from fastapi import APIRouter

from app.routers import auth, categories, comments, notifications, posts, profile, tags, users, ws
from app.routers.autosave import router as autosave_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(profile.router)
api_router.include_router(tags.router)

api_router.include_router(autosave_router)
for router in (
    auth.router,
    users.router,
    categories.router,
    posts.router,
    comments.router,
    notifications.router,
    ws.router,
):
    api_router.include_router(router)
