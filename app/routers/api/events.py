"""
Internal API routes for events.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.routers.api import verify_api_key
from app.services.domain import event_service

router = APIRouter(prefix="/api", tags=["📡 Internal API — Events"], dependencies=[Depends(verify_api_key)])


@router.get("/events/search", summary="Search events")
async def search_events(
    q: str = "",
    city: str = "",
    category: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    price_max: Optional[float] = None,
    is_online: Optional[bool] = None,
):
    """Search for events with filters."""
    return event_service.search_events(
        query=q, city=city, category=category,
        date_from=date_from, date_to=date_to,
        price_max=price_max, is_online=is_online,
    )


@router.get("/events/trending", summary="Get trending events")
async def get_trending_events(city: str = ""):
    """Get trending events in a city."""
    return event_service.get_trending_events(city)


@router.get("/events/{event_source_id}", summary="Get event details")
async def get_event_details(event_source_id: int):
    """Get full details for a specific event."""
    return event_service.get_event_details(event_source_id)


@router.get("/events/{event_source_id}/similar", summary="Get similar events")
async def get_similar_events(
    event_source_id: int,
    category: int = 0,
    city: str = "",
):
    """Get events similar to a given event."""
    return event_service.get_similar_events(event_source_id, category, city)


@router.get("/events/{event_source_id}/reviews", summary="Get event reviews")
async def get_event_reviews(event_source_id: int):
    """Get reviews for an event."""
    from app.services.repositories import review_repo
    rows = review_repo.get_event_reviews(event_source_id)
    if not rows:
        return {"message": "No reviews found.", "reviews": []}
    avg_rating = sum(r.get("rating", 0) for r in rows if r.get("rating")) / len(rows)
    return {
        "event_source_id": event_source_id,
        "review_count": len(rows),
        "average_rating": round(avg_rating, 2),
        "reviews": rows,
    }
