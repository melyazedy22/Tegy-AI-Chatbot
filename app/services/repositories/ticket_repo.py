"""
Ticket repository — all ticket and order SQL queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def get_user_tickets(conn, user_source_id: str) -> list:
    """Get active tickets for a user with event details."""
    sql = """
        SELECT t.booking_code, t.price, t.status, t.seat_number,
               e.name AS event_name, e.start_date, e.end_date,
               e.city, e.place, e.cover_image_url
        FROM tickets t
        JOIN events e ON e.source_id = t.event_source_id
        WHERE t.user_source_id = %s
          AND t.status = 1
        ORDER BY e.start_date ASC
    """
    logger.info(f"[REPO] get_user_tickets user_source_id={user_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] get_user_tickets failed: {e}")
        raise RuntimeError("Failed to query")


def get_user_orders(conn, user_source_id: str) -> list:
    """Get order history for a user."""
    sql = """
        SELECT o.source_id AS order_id, o.total_price, o.status,
               o.payment_method, o.created_at,
               e.name AS event_name, e.start_date, e.city
        FROM orders o
        JOIN events e ON e.source_id = o.event_source_id
        WHERE o.user_source_id = %s
        ORDER BY o.created_at DESC
        LIMIT 10
    """
    logger.info(f"[REPO] get_user_orders user_source_id={user_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] get_user_tickets failed: {e}")
        raise RuntimeError("Failed to query")


def lookup_ticket_by_code(conn, booking_code: str, user_source_id: str) -> list:
    """Look up a specific ticket by booking code, scoped to user."""
    sql = """
        SELECT t.booking_code, t.price, t.status, t.seat_number,
               e.name AS event_name, e.start_date, e.end_date,
               e.city, e.place, e.url, e.is_online
        FROM tickets t
        JOIN events e ON e.source_id = t.event_source_id
        WHERE t.booking_code = %s
          AND t.user_source_id = %s
    """
    logger.info(f"[REPO] lookup_ticket_by_code code={booking_code}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (booking_code, user_source_id))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] get_user_tickets failed: {e}")
        raise RuntimeError("Failed to query")
