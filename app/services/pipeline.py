"""
Chat Pipeline — the main orchestrator.

    User Message
         │
         ▼
    ┌─────────────┐
    │  GUARDRAILS  │ ← scope check
    └──────┬──────┘
           │ pass
           ▼
    ┌─────────────┐
    │   MEMORY     │ ← load conversation + summary + recent msgs
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   PROMPT     │ ← build system prompt with context + user info
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │     LLM      │ ← Groq + function calling (agentic loop)
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   MEMORY     │ ← save messages + maybe update summary
    └──────┘
           │
           ▼
      ChatResponse
"""

import json
import logging
import traceback
from typing import Optional, List, AsyncGenerator

from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.guardrails import is_in_scope, get_out_of_scope_message, has_pii, get_pii_message
from app.services.memory import MemoryService
from app.services.llm_service import llm_service
from app.prompts.system import SYSTEM_PROMPT, SUMMARY_PROMPT, TITLE_PROMPT

logger = logging.getLogger(__name__)


class ChatPipeline:
    """
    Orchestrates the full chat pipeline for a single request.
    Stateless — create a new instance per request.
    """

    def __init__(self):
        self.memory = MemoryService()
        self.sources_used: List[str] = []

    async def process(self, request: ChatRequest) -> ChatResponse:
        """
        Main pipeline entry point.

        Steps:
        1. Scope guardrails
        2. Look up user + get/create conversation
        3. Retrieve memory context (summary + recent messages)
        4. Build system prompt
        5. Call LLM (with function calling)
        6. Save messages
        7. Maybe update summary cache
        8. Return response
        """

        user_message = request.message.strip()

        # ── Step 1: Scope Guardrails ──
        if not is_in_scope(user_message):
            return ChatResponse(
                conversation_id=0,
                reply=get_out_of_scope_message(request.language or "en"),
                sentiment=None,
                suggested_actions=None,
            )

        # ── Step 2: PII Guardrails ──
        if has_pii(user_message):
            return ChatResponse(
                conversation_id=0,
                reply=get_pii_message(request.language or "en"),
                sentiment=None,
                suggested_actions=None,
            )

        # ── Step 3: Look up user + conversation ──
        user = self.memory.get_user(request.user_id)
        conversation = self.memory.get_or_create_conversation(request.user_id, conversation_id=request.conversation_id)
        conv_id = conversation["id"]

        # ── Step 3: Retrieve memory context ──
        context = self.memory.get_context(conv_id)
        self.sources_used = []
        
        # ── Step 3.5: Generate Title for new conversations ──
        if context["message_count"] == 0 and not conversation.get("title") or conversation.get("title") == "New Conversation":
            # Fire and forget title generation
            async def _gen_title():
                prompt = TITLE_PROMPT.format(first_message=user_message)
                title = await llm_service.generate_title(prompt)
                self.memory.update_conversation_title(conv_id, title)
            
            import asyncio
            asyncio.create_task(_gen_title())

        # ── Step 4: Build system prompt ──
        from datetime import datetime
        context_block = self._build_context_block(context)
        system_prompt = SYSTEM_PROMPT.format(
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
            context_block=context_block,
            user_source_id=request.user_id,
            first_name=(user or {}).get("first_name") or "User",
            city=(user or {}).get("city") or "",
            age=(user or {}).get("age") or "",
            gender=(user or {}).get("gender") or "",
            is_organizer=(user or {}).get("is_organizer", False),
            is_verified_organizer=(user or {}).get("is_verified_organizer", False),
            language=request.language or "en",
        )

        # ── Step 5: Call LLM ──
        try:
            bot_reply = await llm_service.chat(
                system_prompt=system_prompt,
                messages=context["recent_messages"],
                user_message=user_message,
            )
            self.sources_used.append("llm")
        except Exception as e:
            traceback.print_exc()
            bot_reply = (
                "I'm sorry, I'm having trouble connecting right now. "
                "Please try again in a moment. 🙏"
            )

        # ── Step 6: Save messages ──
        self.memory.save_message(conv_id, "user", user_message)
        self.memory.save_message(conv_id, "assistant", bot_reply)

        # ── Step 7: Maybe update summary cache ──
        if self.memory.should_update_summary(conv_id):
            await self._update_summary_cache(conv_id, context)

        # ── Build response ──
        # Extract suggestions from the bot reply if it followed the prompt format
        suggested = self._extract_suggestions(bot_reply)
        
        # Clean the reply to remove the [SUGGESTIONS: ...] block before returning to user
        clean_reply = bot_reply.split("[SUGGESTIONS:")[0].strip()

        return ChatResponse(
            conversation_id=conv_id,
            reply=clean_reply,
            sentiment=None,
            suggested_actions=suggested,
            sources_used=self.sources_used if self.sources_used else None,
        )

    async def process_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        Streaming pipeline entry point.
        Yields text chunks as they are generated.
        """

        user_message = request.message.strip()

        # ── Step 1: Scope Guardrails ──
        if not is_in_scope(user_message):
            yield get_out_of_scope_message(request.language or 'en')
            return

        # ── Step 2: PII Guardrails ──
        if has_pii(user_message):
            yield get_pii_message(request.language or 'en')
            return

        # ── Step 3: Look up user + conversation ──
        user = self.memory.get_user(request.user_id)
        conversation = self.memory.get_or_create_conversation(request.user_id, conversation_id=request.conversation_id)
        conv_id = conversation["id"]

        # ── Step 3: Retrieve memory context ──
        context = self.memory.get_context(conv_id)
        
        # ── Step 3.5: Generate Title for new conversations ──
        if context["message_count"] == 0 and not conversation.get("title") or conversation.get("title") == "New Conversation":
            # Fire and forget title generation
            async def _gen_title():
                prompt = TITLE_PROMPT.format(first_message=user_message)
                title = await llm_service.generate_title(prompt)
                self.memory.update_conversation_title(conv_id, title)
            
            import asyncio
            asyncio.create_task(_gen_title())

        # ── Step 4: Build system prompt ──
        from datetime import datetime
        context_block = self._build_context_block(context)
        system_prompt = SYSTEM_PROMPT.format(
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
            context_block=context_block,
            user_source_id=request.user_id,
            first_name=(user or {}).get("first_name") or "User",
            city=(user or {}).get("city") or "",
            age=(user or {}).get("age") or "",
            gender=(user or {}).get("gender") or "",
            is_organizer=(user or {}).get("is_organizer", False),
            is_verified_organizer=(user or {}).get("is_verified_organizer", False),
            language=request.language or "en",
        )

        # ── Step 5: Stream LLM response ──
        full_reply = ""
        try:
            async for chunk in llm_service.chat_stream(
                system_prompt=system_prompt,
                messages=context["recent_messages"],
                user_message=user_message,
            ):
                full_reply += chunk
                yield chunk
        except Exception as e:
            traceback.print_exc()
            fallback = (
                "I'm sorry, I'm having trouble connecting right now. "
                "Please try again in a moment. 🙏"
            )
            full_reply = fallback
            yield fallback

        # ── Step 6: Save messages ──
        self.memory.save_message(conv_id, "user", user_message)
        self.memory.save_message(conv_id, "assistant", full_reply)

        # ── Step 7: Maybe update summary cache ──
        if self.memory.should_update_summary(conv_id):
            await self._update_summary_cache(conv_id, context)

    # ──────── Helpers ────────

    def _build_context_block(self, context: dict) -> str:
        """Build the context block for the system prompt."""
        parts = []

        if context["summary"]:
            parts.append(
                f"**Conversation History Summary:**\n{context['summary']}"
            )
            self.sources_used.append("memory_cache")

        if context["message_count"] > 0:
            parts.append(
                f"(This conversation has {context['message_count']} previous messages)"
            )

        if not parts:
            parts.append("This is a new conversation — no prior context.")

        return "\n\n".join(parts)

    async def _update_summary_cache(self, conv_id: int, previous_context: dict):
        """Regenerate the rolling summary cache."""
        try:
            messages = self.memory.get_unsummarised_messages(conv_id)
            if not messages:
                return

            new_msgs_text = "\n".join(
                f"{m['role'].upper()}: {m['content']}" for m in messages
            )

            prompt = SUMMARY_PROMPT.format(
                previous_summary=previous_context.get("summary") or "None",
                new_messages=new_msgs_text,
            )

            summary = await llm_service.generate_summary(prompt)
            self.memory.update_summary(conv_id, summary)
            logger.info(f"[OK] Summary cache updated for conversation {conv_id}")
        except Exception as e:
            logger.warning(f"[WARN] Failed to update summary: {e}")

    @staticmethod
    def _extract_suggestions(bot_reply: str) -> Optional[List[str]]:
        """Extract the [SUGGESTIONS: A | B | C] block from the LLM's response."""
        if "[SUGGESTIONS:" in bot_reply:
            try:
                # Extract the part between [SUGGESTIONS: and ]
                sugg_str = bot_reply.split("[SUGGESTIONS:")[1].split("]")[0]
                # Split by pipe and clean whitespace
                suggestions = [s.strip() for s in sugg_str.split("|")]
                return [s for s in suggestions if s]
            except Exception:
                pass
        return None
