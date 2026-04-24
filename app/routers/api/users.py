"""
Internal API routes for users.
"""

from fastapi import APIRouter, Depends

from app.routers.api import verify_api_key
from app.services.domain import user_service

router = APIRouter(prefix="/api", tags=["📡 Internal API — Users"], dependencies=[Depends(verify_api_key)])


@router.get("/users/{user_source_id}/recommendations", summary="Get recommendations")
async def get_recommendations(user_source_id: str):
    """Get personalized event recommendations for a user."""
    return user_service.get_recommendations(user_source_id)


@router.get("/users/{user_source_id}/profile", summary="Get user profile")
async def get_user_profile(user_source_id: str):
    """Get user profile details."""
    return user_service.get_user_profile(user_source_id)
