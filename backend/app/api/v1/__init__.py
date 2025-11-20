"""
API v1 Router - Aggregates all API endpoints.
"""

from fastapi import APIRouter

router = APIRouter()

# Import and include routers as they are created
# from app.api.v1.auth import router as auth_router
# from app.api.v1.trips import router as trips_router
# from app.api.v1.conversations import router as conversations_router

# router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# router.include_router(trips_router, prefix="/trips", tags=["Trips"])
# router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])


@router.get("/")
async def api_info():
    """API v1 information endpoint."""
    return {
        "version": "1.0.0",
        "endpoints": [
            "/auth",
            "/trips",
            "/conversations",
            "/chat",
        ]
    }
