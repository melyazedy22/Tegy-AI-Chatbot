"""
Internal API routes for organizer operations.
"""

from fastapi import APIRouter, Depends

from app.routers.api import verify_api_key
from app.services.domain import organizer_service

router = APIRouter(prefix="/api", tags=["📡 Internal API — Organizer"], dependencies=[Depends(verify_api_key)])


@router.get("/organizer/{user_source_id}/events", summary="Get organizer events")
async def get_organizer_events(user_source_id: str):
    """Get all events for an organizer."""
    return organizer_service.get_organizer_events(user_source_id)


@router.get(
    "/organizer/{user_source_id}/events/{event_source_id}/analytics",
    summary="Get event analytics",
)
async def get_event_analytics(user_source_id: str, event_source_id: int):
    """Get analytics for an organizer's event."""
    return organizer_service.get_event_analytics(user_source_id, event_source_id)


@router.get(
    "/organizer/{user_source_id}/events/{event_source_id}/reviews",
    summary="Get organizer event reviews",
)
async def get_event_reviews(user_source_id: str, event_source_id: int):
    """Get reviews for an organizer's event."""
    return organizer_service.get_event_reviews_organizer(user_source_id, event_source_id)
