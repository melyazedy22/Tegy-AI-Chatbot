"""
Internal API routes for interaction logging.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.routers.api import verify_api_key
from app.services.repositories import interaction_repo

router = APIRouter(prefix="/api", tags=["📡 Internal API — Interactions"], dependencies=[Depends(verify_api_key)])


class InteractionRequest(BaseModel):
    user_source_id: str
    event_source_id: int
    action: str  # viewed | loved | shared


@router.post("/interactions", summary="Log user interaction")
async def log_interaction(request: InteractionRequest):
    """Log a user interaction — fire-and-forget, always returns 200."""
    interaction_repo.log_interaction(
        user_source_id=request.user_source_id,
        event_source_id=request.event_source_id,
        action=request.action,
    )
    return {"status": "ok"}
