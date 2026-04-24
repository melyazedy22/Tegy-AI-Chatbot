"""
Support service — business logic for support case operations.
"""

import logging
from app.database.session import get_connection
from app.services.repositories import support_repo

logger = logging.getLogger(__name__)


def open_support_case(
    user_source_id: str,
    subject: str,
    description: str,
    category: str,
    priority: str,
    related_event_source_id: int = None,
    related_order_source_id: int = None,
) -> dict:
    """Create a new support case."""
    # Validate category
    valid_categories = {"billing", "event", "technical", "account", "other"}
    if category not in valid_categories:
        return {"error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"}

    # Validate priority
    valid_priorities = {"low", "medium", "high", "urgent"}
    if priority not in valid_priorities:
        return {"error": f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"}

    try:
        with get_connection() as conn:
            result = support_repo.create_support_case(
                conn=conn,
                user_source_id=user_source_id,
                subject=subject,
                description=description,
                category=category,
                priority=priority,
                related_event_source_id=related_event_source_id,
                related_order_source_id=related_order_source_id,
            )
        if result:
            return {"success": True, "case_id": result.get("id"), "status": "open"}
        return {"error": "Failed to create support case."}
    except Exception as e:
        logger.error(f"[SERVICE] open_support_case failed: {e}")
        return {"error": str(e)}


def get_support_case(case_id: int, user_source_id: str) -> dict:
    """Get a specific support case."""
    try:
        with get_connection() as conn:
            rows = support_repo.get_support_case(conn, case_id, user_source_id)
        if not rows:
            return {"error": "Support case not found."}
        return rows[0]
    except Exception as e:
        logger.error(f"[SERVICE] get_support_case failed: {e}")
        return {"error": str(e)}


def get_user_support_cases(user_source_id: str) -> dict:
    """Get all support cases for a user."""
    try:
        with get_connection() as conn:
            rows = support_repo.get_user_support_cases(conn, user_source_id)
        if not rows:
            return {"message": "No support cases found.", "cases": []}
        return {"cases": rows, "count": len(rows)}
    except Exception as e:
        logger.error(f"[SERVICE] get_user_support_cases failed: {e}")
        return {"error": str(e)}
