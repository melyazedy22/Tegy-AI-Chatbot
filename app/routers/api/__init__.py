"""
Internal API routes package.
Secured with X-Chatbot-Api-Key header.
"""

from fastapi import Header, HTTPException
from app.config import settings


async def verify_api_key(x_chatbot_api_key: str = Header(...)):
    """Shared dependency for API key validation on internal endpoints."""
    if x_chatbot_api_key != settings.chatbot_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return True
