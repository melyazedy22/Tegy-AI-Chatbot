"""
Support tools — LangChain @tool functions for support cases.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

from app.services.domain import support_service

logger = logging.getLogger(__name__)


@tool
def open_support_case(
    user_source_id: str,
    subject: str,
    description: str,
    category: str,
    priority: str,
    related_event_source_id: Optional[int] = None,
    related_order_source_id: Optional[int] = None,
) -> str:
    """
    Open a new support case for the user.
    category: billing | event | technical | account | other
    priority: low | medium | high | urgent
    Always confirm with the user before calling this tool.
    This is the only INSERT operation permitted.

    Args:
        user_source_id: The user's source ID.
        subject: Short description of the issue.
        description: Detailed description of the issue.
        category: Type of issue (billing, event, technical, account, other).
        priority: Priority level (low, medium, high, urgent).
        related_event_source_id: Optional event source ID related to the case.
        related_order_source_id: Optional order source ID related to the case.
    """
    logger.info(f"[TOOL] open_support_case called for user={user_source_id}, cat={category}")
    result = support_service.open_support_case(
        user_source_id=user_source_id,
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        related_event_source_id=related_event_source_id,
        related_order_source_id=related_order_source_id,
    )
    return json.dumps(result, default=str)


@tool
def get_support_case(case_id: int, user_source_id: str) -> str:
    """
    Get details of a specific support case.
    Use for checking the status of a specific support case.

    Args:
        case_id: The support case ID.
        user_source_id: The user's source ID (for ownership check).
    """
    logger.info(f"[TOOL] get_support_case called for case_id={case_id}")
    result = support_service.get_support_case(case_id, user_source_id)
    return json.dumps(result, default=str)


@tool
def get_user_support_cases(user_source_id: str) -> str:
    """
    Get all support cases for a user.
    Use for "my support cases", "did my issue get resolved".

    Args:
        user_source_id: The user's source ID.
    """
    logger.info(f"[TOOL] get_user_support_cases called for user={user_source_id}")
    result = support_service.get_user_support_cases(user_source_id)
    return json.dumps(result, default=str)
