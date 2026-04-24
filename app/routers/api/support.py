"""
Internal API routes for support cases.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.routers.api import verify_api_key
from app.services.domain import support_service

router = APIRouter(prefix="/api", tags=["📡 Internal API — Support"], dependencies=[Depends(verify_api_key)])


class SupportCaseRequest(BaseModel):
    user_source_id: str
    subject: str
    description: str
    category: str
    priority: str
    related_event_source_id: Optional[int] = None
    related_order_source_id: Optional[int] = None


@router.post("/support/cases", summary="Create support case")
async def create_support_case(request: SupportCaseRequest):
    """Create a new support case."""
    return support_service.open_support_case(
        user_source_id=request.user_source_id,
        subject=request.subject,
        description=request.description,
        category=request.category,
        priority=request.priority,
        related_event_source_id=request.related_event_source_id,
        related_order_source_id=request.related_order_source_id,
    )


@router.get("/support/cases/{case_id}", summary="Get support case")
async def get_support_case(
    case_id: int,
    user_source_id: str = Query(...),
):
    """Get a specific support case."""
    return support_service.get_support_case(case_id, user_source_id)


@router.get("/users/{user_source_id}/support/cases", summary="Get user support cases")
async def get_user_support_cases(user_source_id: str):
    """Get all support cases for a user."""
    return support_service.get_user_support_cases(user_source_id)
