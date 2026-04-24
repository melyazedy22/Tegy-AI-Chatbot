# 🎫 Tegy — AI Chatbot for Events & Tickets Platform (Version 2.0.0)

> **Graduation Project** | AI Component — Tegy Chatbot

An intelligent chatbot that provides users with a natural language interface to discover events, manage tickets, track support cases, and get personalized recommendations — powered by live database queries and a large language model.

---

## ✨ Features

- 💬 **Natural Language Q&A** — Ask about events, tickets, orders, and the platform
- 🔧 **18 Live Database Tools** — LLM queries PostgreSQL via function calling
- 🧠 **Persistent Memory** — Rolling summary cache keeps long-term context
- 🌊 **Standardized JSON API** — Clean, easily parseable JSON responses for backend integration (with optional text streaming)
- 🔒 **Security Guardrails** — PII detection and flexible scope guardrails keep conversations safe and on-topic
- ⏱️ **Real-Time Date Awareness** — Live server time injected into LLM for accurate date calculations (e.g. "this weekend")
- 🛡️ **Infinite Loop Detection** — Prevents LLM tool hallucinations and minimizes API rate limits automatically
- 🎯 **Personalized Recommendations** — Based on user interactions
- 👤 **Dual Persona** — Attendee and organizer modes
- 🎫 **Support System** — Open and track support cases through chat
- 🌍 **Arabic & English** — Full bilingual support

---

## 🤖 Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| LLM | Groq — LLaMA 3.3 70B Versatile |
| LLM Orchestration | LangChain + LangChain-Groq |
| Database | PostgreSQL via psycopg2 |
| Config | pydantic-settings + python-dotenv |

---

## 📁 Project Structure

```
Tegy Chatbot/
├── run.py                  ← Start the server
├── requirements.txt        ← Python dependencies
├── .env                    ← Credentials and config
└── app/
    ├── main.py             ← FastAPI app factory
    ├── config.py           ← Settings loader
    ├── routers/
    │   ├── chat.py         ← Chatbot endpoints (6 routes)
    │   └── api/            ← Internal data API (18 routes)
    ├── schemas/
    │   └── chat.py         ← Pydantic models
    ├── prompts/
    │   └── system.py       ← LLM prompt templates
    ├── database/
    │   └── session.py      ← PostgreSQL connection helpers
    └── services/
        ├── pipeline.py     ← Chat orchestrator
        ├── llm_service.py  ← Groq wrapper + streaming
        ├── memory.py       ← Conversation persistence + summary cache
        ├── guardrails.py   ← Domain scope detection
        ├── tools/          ← 18 LangChain tools
        ├── domain/         ← Business logic layer
        └── repositories/   ← Data access layer (SQL)
```

---

## ⚙️ Setup & Running

### Prerequisites
- Python 3.10+
- PostgreSQL database with all tables created
- Groq API key

### Quick Start

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

Edit `.env`:

```env
GROQ_API_KEY=<your_groq_key>
DB_HOST=<postgres_host>
DB_PORT=5432
DB_NAME=<database_name>
DB_USER=<username>
DB_PASSWORD=<password>
CHATBOT_API_KEY=<shared_secret>
```

```bash
python run.py
# Server at http://localhost:8001
# Docs at http://localhost:8001/docs
```

---

## 🔌 API Endpoints

### Chatbot Core

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat/send` | Send message (Returns Standard JSON) |
| `POST` | `/chat/send/stream` | Send message (Raw Text Streaming) |
| `GET` | `/chat/history/{user_id}` | Conversation history |
| `GET` | `/chat/summary/{user_id}` | Memory summary cache |
| `POST` | `/chat/reset/{user_id}` | Reset conversation |

### Internal Data API (`/api` — `X-Chatbot-Api-Key` header required)

18 endpoints for events, users, tickets, support, organizer, and interactions.

---

## 🗄️ Database

Single PostgreSQL database with 9 tables:

| Table | Purpose |
|---|---|
| `users` | Platform user profiles |
| `events` | Event listings |
| `ticket_types` | Event ticket tiers |
| `orders` | Purchase orders |
| `tickets` | Individual tickets + reviews |
| `user_interactions` | Engagement signals (loved/shared/viewed) |
| `support_cases` | Support case tracking |
| `chatbot_conversations` | Conversation sessions |
| `chatbot_messages` | Individual chat messages |

---

## 🏗️ Architecture

```text
User Request → Pipeline → Security Guardrails (PII & Scope) → Memory (context)
    → LLM (Groq + Current Date) → Tools (with Loop Detection) → Services → Context-Managed Repositories → PostgreSQL
    → Standard JSON Response
```

---

## 👨‍💻 Author

**Mahmoud Ramadan Mohamed Elyazedy**
Events & Tickets — AI Graduation Project

