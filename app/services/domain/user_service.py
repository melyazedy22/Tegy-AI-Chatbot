"""
User service — business logic for user operations.
"""

import logging
from app.database.session import get_connection
from app.services.repositories import user_repo

logger = logging.getLogger(__name__)


def get_user_profile(user_source_id: str) -> dict:
    """Get user profile."""
    try:
        with get_connection() as conn:
            rows = user_repo.get_user_profile(conn, user_source_id)
        if not rows:
            return {"error": "User not found."}
        return rows[0]
    except Exception as e:
        logger.error(f"[SERVICE] get_user_profile failed: {e}")
        return {"error": str(e)}


def get_recommendations(user_source_id: str) -> dict:
    """Get personalized event recommendations."""
    try:
        with get_connection() as conn:
            rows = user_repo.get_recommendations(conn, user_source_id)
        if not rows:
            return {"message": "No recommendations available yet. Try interacting with some events!", "results": []}
        return {"results": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_recommendations failed: {e}")
        return {"error": str(e)}
