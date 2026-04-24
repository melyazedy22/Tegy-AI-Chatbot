"""
User repository — all user-related SQL queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def get_user_profile(conn, user_source_id: str) -> list:
    """Get user profile from the main database."""
    sql = """
        SELECT source_id, email, username, first_name, last_name,
               city, age, gender, image_url,
               is_organizer, is_verified_organizer
        FROM users
        WHERE source_id = %s
    """
    logger.info(f"[REPO] get_user_profile user_source_id={user_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] get_user_profile failed: {e}")
        raise RuntimeError("Failed to query")


def get_recommendations(conn, user_source_id: str) -> list:
    """Get personalized event recommendations based on interaction scoring."""
    sql = """
        SELECT e.source_id, e.name, e.city, e.start_date, e.price,
               e.cover_image_url, e.description,
               SUM(CASE WHEN ui.is_loved THEN 3
                        WHEN ui.is_shared THEN 2
                        WHEN ui.is_viewed THEN 1 ELSE 0 END) AS interest_score
        FROM user_interactions ui
        JOIN events e ON e.source_id = ui.event_source_id
        WHERE ui.user_source_id = %s
          AND e.visibility = TRUE AND e.status = 1
          AND e.start_date > NOW()
        GROUP BY e.source_id, e.name, e.city, e.start_date,
                 e.price, e.cover_image_url, e.description
        ORDER BY interest_score DESC
        LIMIT 10
    """
    logger.info(f"[REPO] get_recommendations user_source_id={user_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] get_user_profile failed: {e}")
        raise RuntimeError("Failed to query")
