"""
Pydantic request / response schemas for the Chat API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
#  Request Schemas
# ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    """Incoming message from the frontend."""
    user_id: str = Field(..., description="User source_id from the users table")
    message: str = Field(..., min_length=1, max_length=5000,
                         description="The user's message text")
    language: Optional[str] = Field(default="en",
                                    description="Preferred language: 'en' or 'ar'")
    conversation_id: Optional[int] = Field(
        default=None, 
        description="Optional ID of a specific conversation to continue. If null, continues the active one."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "abc123-def456",
                "message": "What events are happening this weekend?",
                "language": "en",
                "conversation_id": None
            }
        }


# ──────────────────────────────────────────────
#  Response Schemas
# ──────────────────────────────────────────────
class ChatResponse(BaseModel):
    """Bot reply sent to the frontend."""
    conversation_id: int
    reply: str = Field(..., description="The bot's response text")
    sentiment: Optional[str] = Field(None, description="Detected sentiment of user message")
    suggested_actions: Optional[List[str]] = Field(
        default=None,
        description="Quick-reply suggestions for the user"
    )
    sources_used: Optional[List[str]] = Field(
        default=None,
        description="Data sources the bot consulted"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    conversation_id: int
    user_id: str
    message_count: int
    summary: Optional[str]
    messages: List[ConversationHistoryItem]


class ConversationSummaryResponse(BaseModel):
    conversation_id: int
    summary: Optional[str]
    message_count: int
    last_updated: Optional[str] = None


class ConversationListItem(BaseModel):
    id: int
    title: Optional[str]
    summary: Optional[str]
    started_at: str
    ended_at: Optional[str] = None
    is_active: bool

class ConversationListResponse(BaseModel):
    user_id: str
    conversations: List[ConversationListItem]

class RenameConversationRequest(BaseModel):
    title: str = Field(..., description="New title for the conversation")
