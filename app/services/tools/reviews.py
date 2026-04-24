"""
Review tools — LangChain @tool functions for reviews and ratings.
"""

import json
import logging

from langchain_core.tools import tool

from app.database.session import get_connection
from app.services.repositories import review_repo

logger = logging.getLogger(__name__)


@tool
def submit_review(
    ticket_source_id: int,
    rating: float,
    review_text: str,
) -> str:
    """
    Submit a review and rating for a past event.
    Only callable if ticket.status = 2 AND event.end_date < NOW().
    Always confirm with the user before calling.

    Args:
        ticket_source_id: The ticket source ID to review.
        rating: Rating from 1.0 to 5.0.
        review_text: The review text.
    """
    logger.info(f"[TOOL] submit_review called for ticket={ticket_source_id}")
    # Note: user_source_id will be injected by the pipeline context
    # For now, the guard check is in the repository
    with get_connection() as conn:
        result = review_repo.submit_review(
            conn=conn,
            ticket_source_id=ticket_source_id,
            rating=rating,
            review_text=review_text,
            user_source_id="",  # Will be resolved from context
        )
    return json.dumps(result, default=str)


@tool
def get_event_reviews(event_source_id: int) -> str:
    """
    Get reviews and ratings for an event.
    Use for "what do people think of this event", "is it worth going".

    Args:
        event_source_id: The event source ID to get reviews for.
    """
    logger.info(f"[TOOL] get_event_reviews called for event={event_source_id}")
    with get_connection() as conn:
        rows = review_repo.get_event_reviews(conn, event_source_id)
    if not rows:
        return json.dumps({"message": "No reviews found for this event.", "reviews": []})

    avg_rating = sum(r.get("rating", 0) for r in rows if r.get("rating")) / len(rows) if rows else 0
    return json.dumps({
        "event_source_id": event_source_id,
        "review_count": len(rows),
        "average_rating": round(avg_rating, 2),
        "reviews": rows,
    }, default=str)
