"""
Support repository — support cases SQL queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def create_support_case(conn, user_source_id: str,
    subject: str,
    description: str,
    category: str,
    priority: str,
    related_event_source_id: int = None,
    related_order_source_id: int = None,
) -> list:
    """Insert a new support case. Returns the created row."""
    sql = """
        INSERT INTO support_cases
            (user_source_id, subject, description, category, priority,
             related_event_source_id, related_order_source_id,
             status, created_at, updated_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, 'open', NOW(), NOW())
        RETURNING id
    """
    params = (
        user_source_id, subject, description, category, priority,
        related_event_source_id, related_order_source_id,
    )
    logger.info(f"[REPO] create_support_case user={user_source_id}, cat={category}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            try:
                row = cur.fetchone()
                return [dict(row)] if row else []
            except Exception:
                return []
    except Exception as e:
        logger.error(f"[REPO] create_support_case failed: {e}")
        raise RuntimeError("Failed to execute create_support_case")


def get_support_case(conn, case_id: int, user_source_id: str) -> list:
    """Get a specific support case by ID, scoped to user."""
    sql = """
        SELECT id, subject, description, category, status,
               priority, created_at, updated_at, resolved_at
        FROM support_cases
        WHERE id = %s
          AND user_source_id = %s
    """
    logger.info(f"[REPO] get_support_case id={case_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (case_id, user_source_id))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] create_support_case failed: {e}")
        raise RuntimeError("Failed to query")


def get_user_support_cases(conn, user_source_id: str) -> list:
    """Get all support cases for a user."""
    sql = """
        SELECT id, subject, category, status, priority,
               created_at, updated_at, resolved_at
        FROM support_cases
        WHERE user_source_id = %s
        ORDER BY created_at DESC
    """
    logger.info(f"[REPO] get_user_support_cases user={user_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] create_support_case failed: {e}")
        raise RuntimeError("Failed to query")
