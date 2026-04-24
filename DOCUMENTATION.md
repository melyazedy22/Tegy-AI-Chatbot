# 📚 Tegy Chatbot — Full Project Documentation

> Events & Tickets Graduation Project

This document describes every file and folder in the project in detail.

---

## Table of Contents

1. [Root Files](#-root-files)
2. [app/main.py](#-appmainpy)
3. [app/config.py](#-appconfigpy)
4. [app/routers/chat.py](#-approuterschatpy)
5. [app/routers/api/](#-approutersapi)
6. [app/schemas/chat.py](#-appschemaschatpy)
7. [app/prompts/system.py](#-apppromptssystempy)
8. [app/database/session.py](#-appdatabasesessionpy)
9. [app/services/pipeline.py](#-appservicespipelinepy)
10. [app/services/llm_service.py](#-appservicesllm_servicepy)
11. [app/services/memory.py](#-appservicesmemorypy)
12. [app/services/guardrails.py](#-appservicesguardrailspy)
13. [app/services/tools/](#-appservicestools)
14. [app/services/domain/](#-appservicesdomain)
15. [app/services/repositories/](#-appservicesrepositories)

---

## 📂 Root Files

### `run.py`
Entry point. Calls `uvicorn.run()` with host/port from `.env`.

### `requirements.txt`
Key dependencies:
| Package | Why |
|---|---|
| `fastapi` + `uvicorn` | Web framework + ASGI server |
| `langchain-groq` | Groq LLaMA integration |
| `psycopg2-binary` | PostgreSQL connection |
| `pydantic-settings` | Typed settings from `.env` |

### `.env`
All secrets and config. Key values: `GROQ_API_KEY`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `CHATBOT_API_KEY`.

---

## 🚀 `app/main.py`
FastAPI app factory. Registers the chat router and 6 internal API routers. Configures CORS and logging.

## ⚙️ `app/config.py`
Loads `.env` into a typed `Settings` object. All PostgreSQL and Groq credentials centralized here.

---

## 🔌 `app/routers/chat.py`
6 chatbot core endpoints, all prefixed with `/chat`:

| Endpoint | Description |
|---|---|
| `POST /chat/send` | Main endpoint returning structured JSON |
| `POST /chat/send/stream` | Raw text token-by-token streaming |
| `GET /chat/history/{user_id}` | Message history |
| `GET /chat/summary/{user_id}` | Summary cache |
| `POST /chat/reset/{user_id}` | Reset conversation |

## 📡 `app/routers/api/`
18 internal endpoints secured with `X-Chatbot-Api-Key` header, prefixed with `/api`:

| File | Endpoints |
|---|---|
| `events.py` | Search, trending, details, similar, reviews |
| `users.py` | Profile, recommendations |
| `tickets.py` | User tickets, orders, ticket lookup, submit review |
| `support.py` | Create case, get case, list user cases |
| `organizer.py` | Organizer events, analytics, reviews |
| `interactions.py` | Log interaction (fire-and-forget) |

---

## 📐 `app/schemas/chat.py`
Pydantic models: `ChatRequest`, `ChatResponse`, `ConversationHistoryResponse`, `ConversationSummaryResponse`.

## 💬 `app/prompts/system.py`
Three prompt templates: `SYSTEM_PROMPT` (full bot instructions + 18 tool docs + persona rules), `SUMMARY_PROMPT` (conversation compression), `TITLE_PROMPT` (conversation naming).

---

## 🔗 `app/database/session.py`
PostgreSQL connection management via psycopg2 using Python Context Managers:
- `get_connection()` — Yields a `psycopg2` connection object ensuring automatic closing via `try...finally`.
- Used via dependency injection across all repository layers to ensure thread safety and robust lifecycle management.

---

## 🧠 `app/services/pipeline.py`
Main orchestrator. Pipeline steps:
1. **PII check** — prevents sensitive data (Regex detection).
2. **Scope check** — is the message on-topic?
3. **User lookup** — read from `users` table
4. **Conversation** — get/create from `chatbot_conversations`
5. **Context** — load summary + recent messages
6. **Build prompt** — inject user context and live date/time into system prompt
7. **Call LLM** — Groq with tool calling
8. **Save messages** — persist to `chatbot_messages`
9. **Update summary** — regenerate cache every N messages

Methods: `process()` (JSON response), `process_stream()` (streaming).

## 🤖 `app/services/llm_service.py`
Groq LLM wrapper. Methods: `chat()`, `chat_stream()`, `_agentic_loop()`, `_fallback_no_tools()`, `generate_summary()`, `generate_title()`.
Includes an **Infinite Loop Detector** that intercepts repetitive LLM tool hallucinations (calling the same tool with the exact same arguments repeatedly) and injects a strict system command to formulate an answer, bypassing API rate limit freezes.

## 💾 `app/services/memory.py`
Conversation memory using PostgreSQL tables:
- `get_user()` — read from `users`
- `get_or_create_conversation()` — manage `chatbot_conversations`
- `save_message()` — insert into `chatbot_messages`
- `get_context()` — build summary + recent messages payload
- `update_summary()` — update conversation summary cache
- `reset_conversation()` — end current, start new

## 🔍 `app/services/guardrails.py`
- **Scope Detection:** Permissive scope detection. Only blocks clearly off-topic messages. Greetings, short messages, and uncertain queries are allowed through.
- **PII Detection:** Utilizes Regex patterns to intercept messages containing sensitive info (SSNs, Credit Cards, Emails) before processing.

---

## 🔧 `app/services/tools/`
18 LangChain `@tool` functions organized by domain:

| Module | Tools |
|---|---|
| `events.py` | `search_events`, `get_event_details`, `get_similar_events`, `get_trending_events` |
| `users.py` | `get_user_profile`, `get_recommendations` |
| `tickets.py` | `get_user_tickets`, `get_user_orders`, `lookup_ticket_by_code` |
| `support.py` | `open_support_case`, `get_support_case`, `get_user_support_cases` |
| `reviews.py` | `submit_review`, `get_event_reviews` |
| `organizer.py` | `get_organizer_events`, `get_event_analytics`, `get_event_reviews_organizer` |
| `interactions.py` | `log_interaction` |

## 📦 `app/services/domain/`
Business logic layer. Validates inputs and formats outputs:
`event_service.py`, `user_service.py`, `ticket_service.py`, `support_service.py`, `organizer_service.py`.

## 🗄️ `app/services/repositories/`
Data access layer. Raw SQL queries against PostgreSQL:
`event_repo.py`, `user_repo.py`, `ticket_repo.py`, `support_repo.py`, `review_repo.py`, `interaction_repo.py`.

---

## 🗃️ Database Schema

Single PostgreSQL database with 9 tables:

| Table | Purpose |
|---|---|
| `users` | Platform user profiles |
| `events` | Event listings with full-text search |
| `ticket_types` | Event ticket tiers |
| `orders` | Purchase orders |
| `tickets` | Individual tickets + reviews |
| `user_interactions` | Engagement signals (loved/shared/viewed) |
| `support_cases` | Support case tracking |
| `chatbot_conversations` | Conversation sessions with summary cache |
| `chatbot_messages` | Individual chat messages with JSONB metadata |

---

## 🔁 How Everything Connects

```
Frontend / Backend
        │
        ▼
   POST /chat/send
        │
        ▼
   routers/chat.py
        │ creates
        ▼
   services/pipeline.py  ←→  services/memory.py       (PostgreSQL)
        │                ←→  services/guardrails.py    (scope check)
        │                ←→  prompts/system.py         (prompt text)
        │
        ▼
   services/llm_service.py
        │ calls
        ▼
   Groq API (LLaMA 3.3 70B)
        │ calls tools
        ▼
   services/tools/*  →  domain/*  →  repositories/*  →  PostgreSQL
        │
        ▼
   Streaming response back to frontend
```

---

*Documentation for Tegy — Events & Tickets AI Chatbot | Mahmoud Ramadan Mohamed Elyazedy*
