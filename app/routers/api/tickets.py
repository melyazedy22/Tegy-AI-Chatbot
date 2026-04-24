"""
Internal API routes for tickets and orders.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.routers.api import verify_api_key
from app.services.domain import ticket_service
from app.services.repositories import review_repo

router = APIRouter(prefix="/api", tags=["📡 Internal API — Tickets"], dependencies=[Depends(verify_api_key)])


class ReviewRequest(BaseModel):
    rating: float
    review_text: str
    user_source_id: str


@router.get("/users/{user_source_id}/tickets", summary="Get user tickets")
async def get_user_tickets(user_source_id: str):
    """Get active tickets for a user."""
    return ticket_service.get_user_tickets(user_source_id)


@router.get("/users/{user_source_id}/orders", summary="Get user orders")
async def get_user_orders(user_source_id: str):
    """Get order history for a user."""
    return ticket_service.get_user_orders(user_source_id)


@router.get("/tickets/lookup/{booking_code}", summary="Lookup ticket by code")
async def lookup_ticket(
    booking_code: str,
    user_source_id: str = Query(...),
):
    """Look up a ticket by booking code."""
    return ticket_service.lookup_ticket_by_code(booking_code, user_source_id)


@router.post("/tickets/{ticket_source_id}/review", summary="Submit review")
async def submit_review(ticket_source_id: int, request: ReviewRequest):
    """Submit a review for a ticket."""
    result = review_repo.submit_review(
        ticket_source_id=ticket_source_id,
        rating=request.rating,
        review_text=request.review_text,
        user_source_id=request.user_source_id,
    )
    return result
