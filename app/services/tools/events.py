"""
Event tools — LangChain @tool functions for event discovery.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

from app.services.domain import event_service

logger = logging.getLogger(__name__)


@tool
def search_events(
    query: str = "",
    city: str = "",
    category: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    price_max: Optional[float] = None,
    is_online: Optional[bool] = None,
) -> str:
    """
    Search for events by keyword, city, category, date range, price, or online status.
    Use when the user asks about finding events, upcoming events, events in a city,
    or events of a specific type.

    Args:
        query: Search keyword for event name or description.
        city: City name to filter by.
        category: Category number (0=General, 1=Technology, 2=Music, etc.).
        date_from: Start date filter (ISO format, e.g. '2025-01-01').
        date_to: End date filter (ISO format).
        price_max: Maximum price filter.
        is_online: If True, only show online events.
    """
    logger.info(f"[TOOL] search_events called with query={query}, city={city}")
    result = event_service.search_events(
        query=query, city=city, category=category,
        date_from=date_from, date_to=date_to,
        price_max=price_max, is_online=is_online,
    )
    return json.dumps(result, default=str)


@tool
def get_event_details(event_source_id: int) -> str:
    """
    Get full details for a specific event including ticket types.
    Use when the user asks about a specific event's info, ticket types, or availability.

    Args:
        event_source_id: The source ID of the event.
    """
    logger.info(f"[TOOL] get_event_details called with event_source_id={event_source_id}")
    result = event_service.get_event_details(event_source_id)
    return json.dumps(result, default=str)


@tool
def get_similar_events(
    event_source_id: int,
    category: int,
    city: str,
) -> str:
    """
    Get events similar to a given event by category or city.
    Use for "more like this", "other events like this one", or alternatives.

    Args:
        event_source_id: The source ID of the reference event.
        category: The category number of the reference event.
        city: The city of the reference event.
    """
    logger.info(f"[TOOL] get_similar_events called with event_source_id={event_source_id}")
    result = event_service.get_similar_events(event_source_id, category, city)
    return json.dumps(result, default=str)


@tool
def get_trending_events(city: str) -> str:
    """
    Get trending events in a city, ranked by interaction score.
    Use for "what's popular", "most loved", "trending near me".

    Args:
        city: City name to find trending events in.
    """
    logger.info(f"[TOOL] get_trending_events called with city={city}")
    result = event_service.get_trending_events(city)
    return json.dumps(result, default=str)
