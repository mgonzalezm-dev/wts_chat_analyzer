"""
API router initialization
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .conversations import router as conversations_router
from .messages import router as messages_router
from .analytics import router as analytics_router
from .search import router as search_router
from .bookmarks import router as bookmarks_router
from .exports import router as exports_router
from .websocket import router as websocket_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(messages_router, prefix="/messages", tags=["Messages"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(bookmarks_router, prefix="/bookmarks", tags=["Bookmarks"])
api_router.include_router(exports_router, prefix="/exports", tags=["Exports"])
api_router.include_router(websocket_router, tags=["WebSocket"])

__all__ = ["api_router"]