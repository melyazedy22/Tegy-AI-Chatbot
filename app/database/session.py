"""
Database session management.

Single PostgreSQL database for all data:
platform tables (users, events, tickets, etc.) and
chatbot tables (chatbot_conversations, chatbot_messages, support_cases).
"""

import logging
from decimal import Decimal
import psycopg2
import psycopg2.extras

from app.config import settings

logger = logging.getLogger(__name__)


from contextlib import contextmanager

@contextmanager
def get_connection():
    """Returns a psycopg2 connection to the PostgreSQL database as a context manager."""
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        yield conn
    finally:
        conn.close()

def _serialize_row(row: dict) -> dict:
    """Convert non-JSON-serialisable types in a row dict."""
    result = {}
    for key, val in row.items():
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        elif isinstance(val, Decimal):
            val = float(val)
        elif isinstance(val, bytes):
            val = val.hex()
        result[key] = val
    return result

