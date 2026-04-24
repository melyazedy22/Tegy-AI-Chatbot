"""
Centralized configuration — loaded from .env at startup.
All secrets and tunables live here so the rest of the app
never touches os.environ directly.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    # ── Groq LLM ──
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.4"))
    groq_max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", "1024"))

    # ── PostgreSQL Database ──
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")

    # ── Internal API Key ──
    chatbot_api_key: str = os.getenv("CHATBOT_API_KEY", "")

    # ── Chat memory settings ──
    summary_interval: int = int(os.getenv("SUMMARY_INTERVAL", "10"))
    max_recent_messages: int = int(os.getenv("MAX_RECENT_MESSAGES", "6"))
    max_response_length: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))

    # ── Server ──
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
