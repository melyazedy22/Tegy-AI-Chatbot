"""
Review repository — review-related SQL queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def submit_review(conn, ticket_source_id: int,
    rating: float,
    review_text: str,
    user_source_id: str,
) -> list:
    """
    Submit a review for a ticket.
    Guard: only if ticket.status = 2 AND event.end_date < NOW().
    """
    # First check guard conditions
    guard_sql = """
        SELECT t.source_id, t.status, e.end_date
        FROM tickets t
        JOIN events e ON e.source_id = t.event_source_id
        WHERE t.source_id = %s AND t.user_source_id = %s
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(guard_sql, (ticket_source_id, user_source_id))
            rows = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] submit_review check failed: {e}")
        raise RuntimeError("Failed to query")
        
    if not rows:
        return {"error": "Ticket not found or not owned by user."}

    ticket = rows[0]
    if ticket.get("status") != 2:
        return {"error": "You can only review tickets that have been used (status=2)."}

    # end_date is already converted to ISO string by query_db
    # We need to check against NOW() in SQL instead
    check_sql = """
        SELECT 1 FROM tickets t
        JOIN events e ON e.source_id = t.event_source_id
        WHERE t.source_id = %s AND e.end_date < NOW()
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(check_sql, (ticket_source_id,))
            past_check = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] submit_review past_check failed: {e}")
        raise RuntimeError("Failed to query")
        
    if not past_check:
        return {"error": "You can only review past events (event must have ended)."}

    # Submit the review
    sql = """
        UPDATE tickets
        SET rating = %s, review = %s
        WHERE source_id = %s
          AND user_source_id = %s
    """
    logger.info(f"[REPO] submit_review ticket={ticket_source_id}, rating={rating}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (rating, review_text, ticket_source_id, user_source_id))
            conn.commit()
    except Exception as e:
        logger.error(f"[REPO] submit_review failed: {e}")
        raise RuntimeError("Failed to query")
    return {"success": True, "ticket_source_id": ticket_source_id, "rating": rating}


def get_event_reviews(conn, event_source_id: int) -> list:
    """Get reviews for an event."""
    sql = """
        SELECT t.rating, t.review, t.created_at,
               u.first_name, u.last_name
        FROM tickets t
        JOIN users u ON u.source_id = t.user_source_id
        WHERE t.event_source_id = %s
          AND t.review IS NOT NULL
          AND t.rating IS NOT NULL
        ORDER BY t.created_at DESC
        LIMIT 20
    """
    logger.info(f"[REPO] get_event_reviews event_source_id={event_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (event_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] submit_review failed: {e}")
        raise RuntimeError("Failed to query")


def get_event_reviews_organizer(conn, organizer_source_id: str, event_source_id: int
) -> list:
    """Get reviews for an organizer's event."""
    sql = """
        SELECT t.rating, t.review, t.created_at,
               u.first_name, u.last_name
        FROM tickets t
        JOIN events e ON e.source_id = t.event_source_id
        JOIN users u ON u.source_id = t.user_source_id
        WHERE t.event_source_id = %s
          AND e.organizer_source_id = %s
          AND t.review IS NOT NULL
        ORDER BY t.created_at DESC
        LIMIT 50
    """
    logger.info(f"[REPO] get_event_reviews_organizer event={event_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (event_source_id, organizer_source_id))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] submit_review failed: {e}")
        raise RuntimeError("Failed to query")
