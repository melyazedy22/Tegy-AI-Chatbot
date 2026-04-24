"""
Ticket service — business logic for ticket and order operations.
"""

import logging
from app.database.session import get_connection
from app.services.repositories import ticket_repo

logger = logging.getLogger(__name__)


def get_user_tickets(user_source_id: str) -> dict:
    """Get active tickets for a user."""
    try:
        with get_connection() as conn:
            rows = ticket_repo.get_user_tickets(conn, user_source_id)
        if not rows:
            return {"message": "You don't have any active tickets.", "tickets": []}
        return {"tickets": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_user_tickets failed: {e}")
        return {"error": str(e)}


def get_user_orders(user_source_id: str) -> dict:
    """Get order history for a user."""
    try:
        with get_connection() as conn:
            rows = ticket_repo.get_user_orders(conn, user_source_id)
        if not rows:
            return {"message": "No orders found.", "orders": []}
        return {"orders": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_user_orders failed: {e}")
        return {"error": str(e)}


def lookup_ticket_by_code(booking_code: str, user_source_id: str) -> dict:
    """Look up a ticket by booking code."""
    try:
        with get_connection() as conn:
            rows = ticket_repo.lookup_ticket_by_code(conn, booking_code, user_source_id)
        if not rows:
            return {"error": "Ticket not found with that booking code."}
        return rows[0]
    except Exception as e:
        logger.error(f"[SERVICE] lookup_ticket_by_code failed: {e}")
        return {"error": str(e)}
