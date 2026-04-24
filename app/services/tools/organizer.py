"""
Organizer tools — LangChain @tool functions for organizer-only operations.
"""

import json
import logging

from langchain_core.tools import tool

from app.services.domain import organizer_service

logger = logging.getLogger(__name__)


@tool
def get_organizer_events(organizer_source_id: str) -> str:
    """
    Get all events created by an organizer.
    [organizer only] Use for "my events", "show what I've created".
    Only call if is_organizer = true.

    Args:
        organizer_source_id: The organizer's user source ID.
    """
    logger.info(f"[TOOL] get_organizer_events called for organizer={organizer_source_id}")
    result = organizer_service.get_organizer_events(organizer_source_id)
    return json.dumps(result, default=str)


@tool
def get_event_analytics(organizer_source_id: str, event_source_id: int) -> str:
    """
    Get analytics for an organizer's specific event.
    [organizer only] Shows ticket sales, revenue, sell-through rate, avg rating.
    Only call if is_organizer = true.

    Args:
        organizer_source_id: The organizer's user source ID.
        event_source_id: The event source ID to get analytics for.
    """
    logger.info(f"[TOOL] get_event_analytics called for event={event_source_id}")
    result = organizer_service.get_event_analytics(organizer_source_id, event_source_id)
    return json.dumps(result, default=str)


@tool
def get_event_reviews_organizer(
    organizer_source_id: str, event_source_id: int
) -> str:
    """
    Get attendee reviews for an organizer's event.
    [organizer only] Use for reading attendee feedback on a specific event.
    Only call if is_organizer = true.

    Args:
        organizer_source_id: The organizer's user source ID.
        event_source_id: The event source ID to get reviews for.
    """
    logger.info(f"[TOOL] get_event_reviews_organizer called for event={event_source_id}")
    result = organizer_service.get_event_reviews_organizer(
        organizer_source_id, event_source_id
    )
    return json.dumps(result, default=str)
