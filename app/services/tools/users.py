"""
User tools — LangChain @tool functions for user profile and recommendations.
"""

import json
import logging

from langchain_core.tools import tool

from app.services.domain import user_service

logger = logging.getLogger(__name__)


@tool
def get_user_profile(user_source_id: str) -> str:
    """
    Get user profile details from the platform.
    Use for confirming or refreshing user details for personalization.

    Args:
        user_source_id: The user's source ID.
    """
    logger.info(f"[TOOL] get_user_profile called with user_source_id={user_source_id}")
    result = user_service.get_user_profile(user_source_id)
    return json.dumps(result, default=str)


@tool
def get_recommendations(user_source_id: str) -> str:
    """
    Get personalized event recommendations for a user based on their interactions.
    Use for "recommend something", "suggest events for me", "what should I attend".
    Scoring: is_loved*3 + is_shared*2 + is_viewed*1.

    Args:
        user_source_id: The user's source ID.
    """
    logger.info(f"[TOOL] get_recommendations called with user_source_id={user_source_id}")
    result = user_service.get_recommendations(user_source_id)
    return json.dumps(result, default=str)
