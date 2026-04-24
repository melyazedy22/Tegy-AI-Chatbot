"""
Chat API Router — chatbot core endpoints only.
Internal /api routes are in the api/ package.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database.session import get_connection
import psycopg2.extras
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    ConversationHistoryResponse, ConversationHistoryItem,
    ConversationSummaryResponse,
    ConversationListResponse, ConversationListItem,
    RenameConversationRequest
)
from app.services.pipeline import ChatPipeline
from app.services.memory import MemoryService
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["🤖 Chatbot"])


# ──────────────────────────────────────────────
#  Main Chat Endpoint (Non-Streaming JSON)
# ──────────────────────────────────────────────
@router.post(
    "/send",
    response_model=ChatResponse,
    summary="Send a message to Tegy chatbot (JSON response)",
    description=(
        "Send a user message and receive the full JSON response. "
        "This contains all data needed by the backend (conversation_id, reply, suggested_actions)."
    ),
)
async def send_message(request: ChatRequest):
    """Main chat endpoint — returns full response as JSON."""
    pipeline = ChatPipeline()
    return await pipeline.process(request)


# ──────────────────────────────────────────────
#  Streaming Chat (Optional)
# ──────────────────────────────────────────────
@router.post(
    "/send/stream",
    summary="Send a message to Tegy chatbot (streaming)",
    description="Streaming version. Returns text chunks as they generate.",
)
async def send_message_stream(request: ChatRequest):
    """Streaming endpoint — returns raw text stream."""
    pipeline = ChatPipeline()

    async def generate():
        try:
            async for chunk in pipeline.process_stream(request):
                yield chunk
        except Exception:
            yield "I'm sorry, I'm having trouble right now. Please try again."

    return StreamingResponse(generate(), media_type="text/plain")


# ──────────────────────────────────────────────
#  Conversation History
# ──────────────────────────────────────────────
@router.get(
    "/history/{user_id}",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history for a user",
)
async def get_history(user_id: str, conversation_id: int = None, limit: int = 50):
    """Retrieve the message history for a user's active or specific conversation."""
    memory = MemoryService()

    conv = memory.get_or_create_conversation(user_id, conversation_id=conversation_id)
    history = memory.get_conversation_history(conv["id"], limit=limit)
    message_count = memory.get_message_count(conv["id"])

    return ConversationHistoryResponse(
        conversation_id=conv["id"],
        user_id=user_id,
        message_count=message_count,
        summary=conv.get("summary"),
        messages=[
            ConversationHistoryItem(
                role=m["role"],
                content=m["content"],
                timestamp=m["created_at"],
            )
            for m in history
        ],
    )


# ──────────────────────────────────────────────
#  List All Conversations
# ──────────────────────────────────────────────
@router.get(
    "/conversations/{user_id}",
    response_model=ConversationListResponse,
    summary="List all past conversations for a user",
)
async def list_conversations(user_id: str):
    """Retrieve a list of all conversations for a user (like ChatGPT sidebar)."""
    memory = MemoryService()
    conversations = memory.get_user_conversations(user_id)
    
    return ConversationListResponse(
        user_id=user_id,
        conversations=[
            ConversationListItem(
                id=c["id"],
                title=c.get("title") or "New Conversation",
                summary=c.get("summary"),
                started_at=str(c["started_at"]),
                ended_at=str(c["ended_at"]) if c.get("ended_at") else None,
                is_active=c.get("ended_at") is None
            )
            for c in conversations
        ]
    )


# ──────────────────────────────────────────────
#  Rename Conversation
# ──────────────────────────────────────────────
@router.put(
    "/conversations/{conversation_id}/title",
    summary="Rename a conversation manually",
)
async def rename_conversation(conversation_id: int, request: RenameConversationRequest):
    """Update the title of a specific conversation."""
    memory = MemoryService()
    memory.update_conversation_title(conversation_id, request.title)
    return {"status": "ok", "message": "Title updated successfully."}


# ──────────────────────────────────────────────
#  Delete Conversation
# ──────────────────────────────────────────────
@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete a conversation",
)
async def delete_conversation(conversation_id: int):
    """Delete a conversation and its messages entirely."""
    memory = MemoryService()
    memory.delete_conversation(conversation_id)
    return {"status": "ok", "message": "Conversation deleted successfully."}


# ──────────────────────────────────────────────
#  Conversation Summary (the cache)
# ──────────────────────────────────────────────
@router.get(
    "/summary/{user_id}",
    response_model=ConversationSummaryResponse,
    summary="Get the cached conversation summary",
)
async def get_summary(user_id: str):
    """View the current summary cache for a user's conversation."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, summary, started_at
                FROM chatbot_conversations
                WHERE user_source_id = %s AND ended_at IS NULL
                ORDER BY started_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            rows = [dict(r) for r in cur.fetchall()]

    if not rows:
        raise HTTPException(status_code=404, detail="No active conversation found.")

    conv = rows[0]
    memory = MemoryService()
    message_count = memory.get_message_count(conv["id"])

    return ConversationSummaryResponse(
        conversation_id=conv["id"],
        summary=conv.get("summary"),
        message_count=message_count,
        last_updated=conv.get("started_at"),
    )


# ──────────────────────────────────────────────
#  Reset Conversation
# ──────────────────────────────────────────────
@router.post(
    "/reset/{user_id}",
    summary="Reset / start a new conversation",
    description="Ends the current conversation and starts a fresh one.",
)
async def reset_conversation(user_id: str):
    """End current conversation and start a new one."""
    memory = MemoryService()
    new_conv = memory.reset_conversation(user_id)
    return {
        "status": "ok",
        "message": "Conversation reset. Starting fresh!",
        "new_conversation_id": new_conv["id"],
    }
