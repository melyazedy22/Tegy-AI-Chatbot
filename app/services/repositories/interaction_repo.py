"""
Interaction repository — user interaction logging queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def log_interaction(conn, user_source_id: str, event_source_id: int, action: str
) -> list:
    """
    Log a user interaction (viewed/loved/shared) with upsert.
    Fire-and-forget — always returns immediately.
    """
    is_viewed = action == "viewed"
    is_loved = action == "loved"
    is_shared = action == "shared"

    sql = """
        INSERT INTO user_interactions
            (user_source_id, event_source_id,
             is_viewed, is_loved, is_shared,
             view_time_sec, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, 0, NOW(), NOW())
        ON CONFLICT (user_source_id, event_source_id)
        DO UPDATE SET
            is_loved  = user_interactions.is_loved  OR EXCLUDED.is_loved,
            is_shared = user_interactions.is_shared OR EXCLUDED.is_shared,
            is_viewed = user_interactions.is_viewed OR EXCLUDED.is_viewed,
            updated_at = NOW()
    """
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (
                user_source_id, event_source_id,
                is_viewed, is_loved, is_shared,
            ))
            conn.commit()
        logger.info(f"[REPO] log_interaction user={user_source_id}, event={event_source_id}, action={action}")
    except Exception as e:
        logger.error(f"[REPO] log_interaction failed: {e}")

    return {"status": "ok"}
