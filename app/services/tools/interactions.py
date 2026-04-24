"""
Interaction tools — LangChain @tool function for logging user interactions.
"""

import json
import logging

from langchain_core.tools import tool

from app.database.session import get_connection
from app.services.repositories import interaction_repo

logger = logging.getLogger(__name__)


@tool
def log_interaction(
    user_source_id: str,
    event_source_id: int,
    action: str,
) -> str:
    """
    Log a user interaction with an event (viewed, loved, or shared).
    Call silently in the background — never mention to the user.
    Fire-and-forget — never display the result.
    These signals feed directly into get_recommendations scoring.

    Args:
        user_source_id: The user's source ID.
        event_source_id: The event source ID.
        action: One of: viewed | loved | shared.
    """
    logger.info(f"[TOOL] log_interaction called: user={user_source_id}, event={event_source_id}, action={action}")
    with get_connection() as conn:
        result = interaction_repo.log_interaction(conn, user_source_id, event_source_id, action)
    return json.dumps(result, default=str)
