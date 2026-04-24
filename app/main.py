"""
FastAPI application — entry point.

Tegy 🎫 — AI Chatbot for Events & Tickets Platform
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.chat import router as chat_router
from app.routers.api.events import router as events_api_router
from app.routers.api.users import router as users_api_router
from app.routers.api.tickets import router as tickets_api_router
from app.routers.api.support import router as support_api_router
from app.routers.api.organizer import router as organizer_api_router
from app.routers.api.interactions import router as interactions_api_router

# ── Configure logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ──────────────────────────────────────────────
#  App factory
# ──────────────────────────────────────────────
app = FastAPI(
    title="Tegy 🎫 — Events & Tickets Chatbot API",
    description=(
        "AI-powered chatbot for the Events & Tickets platform.\n\n"
        "**Features:**\n"
        "- Natural language Q&A about events, tickets, and the platform\n"
        "- Live PostgreSQL queries via 18 function-calling tools\n"
        "- Conversation memory with summary caching\n"
        "- Scope-based guardrails\n"
        "- Streaming responses\n"
        "- Arabic & English language support\n\n"
        "**Powered by:** Groq (LLaMA 3.3 70B) + LangChain\n\n"
        "**Events & Tickets — Graduation Project**"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──
app.include_router(chat_router)
app.include_router(events_api_router)
app.include_router(users_api_router)
app.include_router(tickets_api_router)
app.include_router(support_api_router)
app.include_router(organizer_api_router)
app.include_router(interactions_api_router)


# ── Startup event ──
@app.on_event("startup")
async def on_startup():
    """Log startup info."""
    print("=" * 50)
    print("  Tegy Chatbot is LIVE!")
    print(f"  Model: {settings.groq_model}")
    print(f"  Docs:  http://{settings.host}:{settings.port}/docs")
    print("=" * 50)


# ── Root endpoint ──
@app.get("/", tags=["General"])
def root():
    return {
        "name": "Tegy 🎫 — Events & Tickets Chatbot",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running",
    }
