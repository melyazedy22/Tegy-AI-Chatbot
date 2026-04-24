"""
Chat memory service — manages conversation persistence and summary cache.

All data lives in the PostgreSQL database:
- users                  → platform user profile (read-only)
- chatbot_conversations  → conversation sessions
- chatbot_messages       → individual messages

Key idea: instead of sending the entire chat history to the LLM,
we maintain a rolling summary (the "cache") and only include
the last N messages for recency.
"""

import json
import logging
from typing import Optional, List, Dict

from app.config import settings
from app.database.session import get_connection
import psycopg2.extras

logger = logging.getLogger(__name__)

def _query_db(sql: str, params: tuple = ()) -> list:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

def _execute_db(sql: str, params: tuple = ()) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            conn.commit()
            try:
                row = cur.fetchone()
                return dict(row) if row else None
            except psycopg2.ProgrammingError:
                return None


class MemoryService:
    """Manages chat memory — persistence + summary cache."""

    # ─────── User Lookup ───────

    def get_user(self, user_source_id: str) -> Optional[dict]:
        """Look up a user from the users table (read-only)."""
        rows = _query_db(
            """
            SELECT source_id, email, username, first_name, last_name,
                   city, age, gender, image_url,
                   is_organizer, is_verified_organizer
            FROM users
            WHERE source_id = %s
            """,
            (user_source_id,),
        )
        return rows[0] if rows else None

    # ─────── Conversation Management ───────

    def get_or_create_conversation(
        self, user_source_id: str, channel: str = "web", conversation_id: Optional[int] = None
    ) -> dict:
        """Get user's specific conversation, active conversation, or create one."""
        if conversation_id:
            # Try to fetch the specific conversation provided
            rows = _query_db(
                """
                SELECT id, user_source_id, started_at, ended_at, summary, title, channel
                FROM chatbot_conversations
                WHERE id = %s AND user_source_id = %s
                """,
                (conversation_id, user_source_id),
            )
            if rows:
                return rows[0]
                
        # Fallback to fetching the latest active conversation
        rows = _query_db(
            """
            SELECT id, user_source_id, started_at, ended_at, summary, title, channel
            FROM chatbot_conversations
            WHERE user_source_id = %s AND ended_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (user_source_id,),
        )
        if rows:
            return rows[0]

        # Create new conversation
        result = _execute_db(
            """
            INSERT INTO chatbot_conversations (user_source_id, channel, title)
            VALUES (%s, %s, 'New Conversation')
            RETURNING id, user_source_id, started_at, ended_at, summary, title, channel
            """,
            (user_source_id, channel),
        )
        logger.info(f"[MEMORY] Created conversation for user={user_source_id}")
        return result

    def update_conversation_title(self, conversation_id: int, title: str):
        """Update the title of a conversation."""
        _execute_db(
            "UPDATE chatbot_conversations SET title = %s WHERE id = %s",
            (title, conversation_id)
        )

    def delete_conversation(self, conversation_id: int):
        """Delete a conversation and all its associated messages."""
        # Delete messages first (in case ON DELETE CASCADE is missing)
        _execute_db("DELETE FROM chatbot_messages WHERE conversation_id = %s", (conversation_id,))
        # Delete the conversation itself
        _execute_db("DELETE FROM chatbot_conversations WHERE id = %s", (conversation_id,))

    # ─────── Message Persistence ───────

    def save_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict | None:
        """Save a message to chatbot_messages."""
        meta_json = json.dumps(metadata) if metadata else None
        result = _execute_db(
            """
            INSERT INTO chatbot_messages
                (conversation_id, role, content, metadata, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id, conversation_id, role, content, created_at
            """,
            (conversation_id, role, content, meta_json),
        )
        return result

    # ─────── Context Retrieval ───────

    def get_context(self, conversation_id: int) -> Dict:
        """
        Build the context payload for the LLM prompt.

        Returns
        -------
        {
            "summary": str | None,
            "recent_messages": [ {"role": ..., "content": ...} ],
            "message_count": int,
        }
        """
        max_recent = settings.max_recent_messages

        # Get conversation summary
        conv_rows = _query_db(
            "SELECT summary FROM chatbot_conversations WHERE id = %s",
            (conversation_id,),
        )
        summary = conv_rows[0]["summary"] if conv_rows else None

        # Get recent messages
        recent = _query_db(
            """
            SELECT role, content, created_at
            FROM chatbot_messages
            WHERE conversation_id = %s AND role IN ('user', 'assistant')
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (conversation_id, max_recent),
        )
        recent.reverse()  # chronological order

        # Get total count
        count_rows = _query_db(
            "SELECT COUNT(*) AS cnt FROM chatbot_messages WHERE conversation_id = %s",
            (conversation_id,),
        )
        message_count = count_rows[0]["cnt"] if count_rows else 0

        return {
            "summary": summary,
            "recent_messages": [
                {"role": m["role"], "content": m["content"]}
                for m in recent
            ],
            "message_count": message_count,
        }

    def get_unsummarised_messages(self, conversation_id: int) -> List[dict]:
        """Get all messages in the conversation for summary generation."""
        return _query_db(
            """
            SELECT role, content
            FROM chatbot_messages
            WHERE conversation_id = %s AND role IN ('user', 'assistant')
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )

    def get_message_count(self, conversation_id: int) -> int:
        """Count messages in a conversation."""
        rows = _query_db(
            "SELECT COUNT(*) AS cnt FROM chatbot_messages WHERE conversation_id = %s",
            (conversation_id,),
        )
        return rows[0]["cnt"] if rows else 0

    def should_update_summary(self, conversation_id: int) -> bool:
        """Check if it's time to regenerate the summary cache."""
        count = self.get_message_count(conversation_id)
        return count > 0 and count % settings.summary_interval == 0

    def update_summary(self, conversation_id: int, new_summary: str):
        """Store the new summary cache."""
        _execute_db(
            """
            UPDATE chatbot_conversations
            SET summary = %s
            WHERE id = %s
            """,
            (new_summary, conversation_id),
        )
        logger.info(f"[MEMORY] Summary updated for conversation {conversation_id}")

    # ─────── History Retrieval (for API) ───────

    def get_conversation_history(
        self, conversation_id: int, limit: int = 50
    ) -> List[Dict]:
        """Get full message history for display."""
        return _query_db(
            """
            SELECT role, content, created_at
            FROM chatbot_messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (conversation_id, limit),
        )

    def get_user_conversations(self, user_source_id: str) -> List[Dict]:
        """Get a list of all conversations for a user, sorted by most recent."""
        return _query_db(
            """
            SELECT id, title, started_at, ended_at
            FROM chatbot_conversations
            WHERE user_source_id = %s
            ORDER BY started_at DESC
            """,
            (user_source_id,),
        )

    # ─────── Cleanup ───────

    def reset_conversation(
        self, user_source_id: str, channel: str = "web"
    ) -> dict:
        """End current conversation and start a new one."""
        # End all active conversations
        _execute_db(
            """
            UPDATE chatbot_conversations
            SET ended_at = NOW()
            WHERE user_source_id = %s AND ended_at IS NULL
            """,
            (user_source_id,),
        )
        # Create fresh conversation
        return self.get_or_create_conversation(user_source_id, channel)
