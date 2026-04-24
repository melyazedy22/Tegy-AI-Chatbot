"""
Organizer service — business logic for organizer-specific operations.
"""

import logging
from app.database.session import get_connection
import psycopg2.extras
from app.services.repositories import review_repo

logger = logging.getLogger(__name__)


def get_organizer_events(organizer_source_id: str) -> dict:
    """Get all events for an organizer."""
    try:
        sql = """
            SELECT source_id, name, start_date, end_date, city,
                   status, total_tickets, ticket_count,
                   (total_tickets - ticket_count) AS remaining,
                   cover_image_url
            FROM events
            WHERE organizer_source_id = %s
            ORDER BY start_date DESC
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (organizer_source_id,))
                rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return {"message": "No events found.", "events": []}
        return {"events": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_organizer_events failed: {e}")
        return {"error": str(e)}


def get_event_analytics(organizer_source_id: str, event_source_id: int) -> dict:
    """Get analytics for a specific organizer event."""
    try:
        sql = """
            SELECT e.name, e.start_date, e.total_tickets, e.ticket_count,
                   (e.total_tickets - e.ticket_count) AS remaining,
                   ROUND(e.ticket_count::DECIMAL /
                         NULLIF(e.total_tickets, 0) * 100, 1) AS sell_through_pct,
                   AVG(t.rating)        AS avg_rating,
                   COUNT(t.review)      AS review_count,
                   SUM(t.price)         AS total_revenue
            FROM events e
            LEFT JOIN tickets t ON t.event_source_id = e.source_id
            WHERE e.source_id = %s
              AND e.organizer_source_id = %s
            GROUP BY e.name, e.start_date, e.total_tickets, e.ticket_count
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (event_source_id, organizer_source_id))
                rows = [dict(r) for r in cur.fetchall()]
        if not rows:
            return {"error": "Event not found or not owned by organizer."}
        return rows[0]
    except Exception as e:
        logger.error(f"[SERVICE] get_event_analytics failed: {e}")
        return {"error": str(e)}


def get_event_reviews_organizer(
    organizer_source_id: str, event_source_id: int
) -> dict:
    """Get reviews for an organizer's event."""
    try:
        with get_connection() as conn:
            rows = review_repo.get_event_reviews_organizer(
                conn, organizer_source_id, event_source_id
            )
        if not rows:
            return {"message": "No reviews yet for this event.", "reviews": []}
        return {"reviews": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_event_reviews_organizer failed: {e}")
        return {"error": str(e)}
