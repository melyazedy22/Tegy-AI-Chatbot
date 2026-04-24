"""
Event repository — all event-related SQL queries.
"""

import logging
import psycopg2.extras

logger = logging.getLogger(__name__)


def search_events(conn, query: str = "",
    city: str = "",
    category: int = None,
    date_from: str = None,
    date_to: str = None,
    price_max: float = None,
    is_online: bool = None,
) -> list:
    """Search for active public upcoming events with filters."""
    conditions = [
        "visibility = TRUE",
        "status = 1",
        "start_date > NOW()",
    ]
    params = []

    if query and query.strip():
        conditions.append(
            "to_tsvector('english', name || ' ' || description) "
            "@@ plainto_tsquery('english', %s)"
        )
        params.append(query.strip())

    if city and city.strip():
        conditions.append("city ILIKE %s")
        params.append(f"%{city.strip()}%")

    if category is not None:
        conditions.append("category = %s")
        params.append(category)

    if date_from:
        conditions.append("start_date >= %s")
        params.append(date_from)

    if date_to:
        conditions.append("start_date <= %s")
        params.append(date_to)

    if price_max is not None:
        conditions.append("price <= %s")
        params.append(price_max)

    if is_online is not None:
        conditions.append("is_online = %s")
        params.append(is_online)

    where = " AND ".join(conditions)
    sql = f"""
        SELECT source_id, name, description, city, start_date, price,
               cover_image_url, is_online, place,
               (total_tickets - ticket_count) AS available_tickets
        FROM events
        WHERE {where}
        ORDER BY start_date ASC
        LIMIT 10
    """
    logger.info(f"[REPO] search_events query={query}, city={city}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, tuple(params))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] search_events failed: {e}")
        raise RuntimeError("Failed to query")


def get_event_details(conn, event_source_id: int) -> list:
    """Get full event details with ticket types."""
    sql = """
        SELECT e.*, tt.name AS ticket_type_name, tt.price AS ticket_type_price,
               tt.capacity, tt.limit_per_user, tt.description AS ticket_type_desc
        FROM events e
        LEFT JOIN ticket_types tt ON tt.event_source_id = e.source_id
        WHERE e.source_id = %s
          AND e.visibility = TRUE
    """
    logger.info(f"[REPO] get_event_details source_id={event_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (event_source_id,))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] search_events failed: {e}")
        raise RuntimeError("Failed to query")


def get_similar_events(conn, event_source_id: int, category: int, city: str
) -> list:
    """Get similar events by category or city."""
    sql = """
        SELECT source_id, name, city, start_date, price, cover_image_url
        FROM events
        WHERE visibility = TRUE AND status = 1
          AND start_date > NOW()
          AND source_id != %s
          AND (category = %s OR city ILIKE %s)
        ORDER BY start_date ASC
        LIMIT 10
    """
    logger.info(f"[REPO] get_similar_events source_id={event_source_id}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (event_source_id, category, f"%{city}%"))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] search_events failed: {e}")
        raise RuntimeError("Failed to query")


def get_trending_events(conn, city: str) -> list:
    """Get trending events ranked by interaction score."""
    sql = """
        SELECT e.source_id, e.name, e.city, e.start_date, e.price,
               e.cover_image_url,
               SUM(CASE WHEN ui.is_loved THEN 3
                        WHEN ui.is_shared THEN 2
                        WHEN ui.is_viewed THEN 1 ELSE 0 END) AS trend_score
        FROM events e
        JOIN user_interactions ui ON ui.event_source_id = e.source_id
        WHERE e.visibility = TRUE AND e.status = 1
          AND e.start_date > NOW()
          AND e.city ILIKE %s
        GROUP BY e.source_id, e.name, e.city, e.start_date,
                 e.price, e.cover_image_url
        ORDER BY trend_score DESC
        LIMIT 10
    """
    logger.info(f"[REPO] get_trending_events city={city}")
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (f"%{city}%",))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"[REPO] search_events failed: {e}")
        raise RuntimeError("Failed to query")
