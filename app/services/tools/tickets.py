"""
Ticket tools — LangChain @tool functions for tickets and orders.
"""

import json
import logging

from langchain_core.tools import tool

from app.services.domain import ticket_service

logger = logging.getLogger(__name__)


@tool
def get_user_tickets(user_source_id: str) -> str:
    """
    Get active tickets for a user with event details.
    Use for "my tickets", "upcoming events I'm going to", "my bookings".
    Returns active tickets (status=1) joined with event details.

    Args:
        user_source_id: The user's source ID.
    """
    logger.info(f"[TOOL] get_user_tickets called with user_source_id={user_source_id}")
    result = ticket_service.get_user_tickets(user_source_id)
    return json.dumps(result, default=str)


@tool
def get_user_orders(user_source_id: str) -> str:
    """
    Get order history for a user.
    Use for "my orders", "purchase history", "what did I spend".

    Args:
        user_source_id: The user's source ID.
    """
    logger.info(f"[TOOL] get_user_orders called with user_source_id={user_source_id}")
    result = ticket_service.get_user_orders(user_source_id)
    return json.dumps(result, default=str)


@tool
def lookup_ticket_by_code(booking_code: str, user_source_id: str) -> str:
    """
    Look up a specific ticket by its booking code.
    Always scoped to current user — never returns another user's ticket.

    Args:
        booking_code: The booking code to look up.
        user_source_id: The user's source ID (for ownership check).
    """
    logger.info(f"[TOOL] lookup_ticket_by_code called with code={booking_code}")
    result = ticket_service.lookup_ticket_by_code(booking_code, user_source_id)
    return json.dumps(result, default=str)
