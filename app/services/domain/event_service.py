"""
Event service — business logic for event operations.
"""

import json
import logging
from app.database.session import get_connection
from app.services.repositories import event_repo

logger = logging.getLogger(__name__)


def search_events(
    query: str = "",
    city: str = "",
    category: int = None,
    date_from: str = None,
    date_to: str = None,
    price_max: float = None,
    is_online: bool = None,
) -> dict:
    """Search for events with filters. Returns formatted result."""
    try:
        with get_connection() as conn:
            rows = event_repo.search_events(
                conn, query=query, city=city, category=category,
                date_from=date_from, date_to=date_to,
                price_max=price_max, is_online=is_online,
            )
        if not rows:
            return {"message": "No events found matching your criteria.", "results": []}
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] search_events failed: {e}")
        return {"error": f"Failed to search events: {str(e)}"}


def get_event_details(event_source_id: int) -> dict:
    """Get full details for a specific event."""
    try:
        with get_connection() as conn:
            rows = event_repo.get_event_details(conn, event_source_id)
        if not rows:
            return {"error": f"Event not found."}
        # Group ticket types
        event_data = {k: v for k, v in rows[0].items()
                      if not k.startswith("ticket_type_")}
        ticket_types = []
        for row in rows:
            if row.get("ticket_type_name"):
                ticket_types.append({
                    "name": row["ticket_type_name"],
                    "price": row["ticket_type_price"],
                    "capacity": row.get("capacity"),
                    "limit_per_user": row.get("limit_per_user"),
                    "description": row.get("ticket_type_desc"),
                })
        event_data["ticket_types"] = ticket_types
        return event_data
    except Exception as e:
        logger.error(f"[SERVICE] get_event_details failed: {e}")
        return {"error": str(e)}


def get_similar_events(
    event_source_id: int, category: int, city: str
) -> dict:
    """Get similar events by category or city."""
    try:
        with get_connection() as conn:
            rows = event_repo.get_similar_events(conn, event_source_id, category, city)
        if not rows:
            return {"message": "No similar events found.", "results": []}
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_similar_events failed: {e}")
        return {"error": str(e)}


def get_trending_events(city: str) -> dict:
    """Get trending events in a city."""
    try:
        with get_connection() as conn:
            rows = event_repo.get_trending_events(conn, city)
        if not rows:
            return {"message": "No trending events found.", "results": []}
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_trending_events failed: {e}")
        return {"error": str(e)}
