"""
LLM Service — Groq integration via LangChain.

Handles:
- Chat completions with function calling (streaming)
- Summary generation
- Title generation
- Graceful fallback when tool-calling fails
"""

import logging
import traceback
from typing import List, Dict, Optional, AsyncGenerator

from langchain_groq import ChatGroq
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, ToolMessage,
)

from app.config import settings
from app.services.tools import get_all_tools

logger = logging.getLogger(__name__)


class LLMService:
    """Wrapper around Groq LLM with tool-calling and streaming support."""

    def __init__(self):
        # Primary
        self._llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
            max_retries=0,
            streaming=True,
        )

        # Load tools
        all_tools = get_all_tools()

        # Bind function-calling tools
        self._llm_with_tools = self._llm.bind_tools(all_tools)

        # Build tool lookup for execution
        self._tool_map = {tool.name: tool for tool in all_tools}

    async def chat(
        self,
        system_prompt: str,
        messages: List[Dict],
        user_message: str,
    ) -> str:
        """
        Send a chat completion request with tool calling support.

        If the LLM produces an invalid tool call (Groq returns 400),
        we retry once WITHOUT tools so the user still gets a response.
        """
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        lc_messages.append(HumanMessage(content=user_message))

        try:
            return await self._agentic_loop(lc_messages)
        except Exception as e:
            error_str = str(e).lower()
            if "tool_use_failed" in error_str or "failed to call" in error_str:
                logger.warning(f"[LLM] Tool-call failed, retrying without tools: {e}")
                return await self._fallback_no_tools(lc_messages)
            if "rate_limit" in error_str or "429" in error_str:
                logger.warning(f"[LLM] Rate limited, retrying without tools: {e}")
                return await self._fallback_no_tools(lc_messages)
            raise

    async def chat_stream(
        self,
        system_prompt: str,
        messages: List[Dict],
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming version of chat.
        First runs tool calls to completion, then streams the final text response.
        Falls back to non-streaming if streaming fails.
        """
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        lc_messages.append(HumanMessage(content=user_message))

        try:
            # First, do tool loop (not streamed)
            final_messages = await self._agentic_loop_for_stream(lc_messages)

            # Now stream the final response
            async for chunk in self._llm_with_tools.astream(final_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.warning(f"[LLM] Streaming failed, falling back: {e}")
            # Fallback to non-streaming
            try:
                result = await self._fallback_no_tools(lc_messages)
                yield result
            except Exception:
                yield "I'm sorry, I'm having trouble processing your request. Please try again shortly."

    async def _agentic_loop(self, lc_messages: list) -> str:
        """Run the tool-calling agentic loop (max 5 iterations)."""
        max_iterations = 5
        response = None
        executed_calls = set()

        for _ in range(max_iterations):
            try:
                response = await self._llm_with_tools.ainvoke(lc_messages)
            except Exception as e:
                # If the LLM fails with a tool call error mid-loop, break and fallback
                if "tool_use_failed" in str(e).lower():
                    raise
                raise

            lc_messages.append(response)

            # If no tool calls, we have the final response
            if not response.tool_calls:
                return response.content or "I'm sorry, I couldn't generate a response."

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                call_signature = f"{tool_name}:{str(tool_args)}"

                if call_signature in executed_calls:
                    logger.warning(f"[LLM] Loop detected, blocking duplicate call: {tool_name}({tool_args})")
                    result = "SYSTEM INSTRUCTION: You just called this tool with these exact parameters. DO NOT call it again. Formulate your final answer to the user now."
                else:
                    executed_calls.add(call_signature)
                    logger.info(f"[LLM] Tool call: {tool_name}({tool_args})")

                tool_fn = self._tool_map.get(tool_name)
                if tool_fn:
                    try:
                        result = tool_fn.invoke(tool_args)
                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"
                        logger.error(f"[LLM] Tool execution error: {e}")
                else:
                    result = f"Unknown tool: {tool_name}"

                lc_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

        # Fallback if max iterations reached
        return (response.content if response else "") or \
               "I apologise, I had trouble processing your request. Please try again."

    async def _agentic_loop_for_stream(self, lc_messages: list) -> list:
        """
        Run tool-calling loop and return the message list
        ready for final streaming response.
        """
        max_iterations = 5
        executed_calls = set()

        for _ in range(max_iterations):
            response = await self._llm_with_tools.ainvoke(lc_messages)
            lc_messages.append(response)

            if not response.tool_calls:
                # Remove the last AI response (we'll re-stream it)
                lc_messages.pop()
                return lc_messages

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                call_signature = f"{tool_name}:{str(tool_args)}"

                if call_signature in executed_calls:
                    logger.warning(f"[LLM] Loop detected, blocking duplicate call: {tool_name}({tool_args})")
                    result = "SYSTEM INSTRUCTION: You just called this tool with these exact parameters. DO NOT call it again. Formulate your final answer to the user now."
                else:
                    executed_calls.add(call_signature)
                    logger.info(f"[LLM] Tool call (stream prep): {tool_name}({tool_args})")

                tool_fn = self._tool_map.get(tool_name)
                if tool_fn:
                    try:
                        result = tool_fn.invoke(tool_args)
                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"
                else:
                    result = f"Unknown tool: {tool_name}"

                lc_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

        return lc_messages

    async def _fallback_no_tools(self, lc_messages: list) -> str:
        """Fallback: call the LLM without tools bound."""
        try:
            # Add a hint to the last user message
            lc_messages.append(HumanMessage(
                content=(
                    "[System note: answer the user's question directly using your "
                    "knowledge and the conversation context. Do not attempt to call tools.]"
                )
            ))
            response = self._llm.invoke(lc_messages)
            return response.content or "I'm sorry, I couldn't generate a response right now."
        except Exception as e:
            logger.error(f"[LLM] Fallback also failed: {e}")
            return "I'm sorry, I'm having trouble processing your request. Please try again shortly."

    async def generate_summary(self, prompt: str) -> str:
        """Generate a conversation summary (no tools needed)."""
        response = self._llm.invoke([HumanMessage(content=prompt)])
        return response.content or ""

    async def generate_title(self, prompt: str) -> str:
        """Generate a short conversation title."""
        response = self._llm.invoke([HumanMessage(content=prompt)])
        title = response.content or "Chat"
        return title.strip().strip('"').strip("'")[:100]

    async def generate_suggestions(self, bot_reply: str, language: str) -> list[str]:
        """Generate smart quick-reply suggestions based on the bot's own reply."""
        try:
            prompt = (
                f"Based on the following message from an AI assistant, suggest 3 short, "
                f"actionable quick-reply phrases the user could click to continue the conversation.\n"
                f"The suggestions must be in {'Arabic' if language == 'ar' else 'English'}.\n"
                f"Output ONLY a comma-separated list of the 3 phrases. No numbering, no introduction.\n\n"
                f"Assistant message: {bot_reply}"
            )
            response = self._llm.invoke([HumanMessage(content=prompt)])
            text = response.content or ""
            
            # Parse the comma-separated list
            suggestions = [s.strip().strip('"').strip("'") for s in text.split(',')]
            suggestions = [s for s in suggestions if len(s) > 2][:3]
            
            if len(suggestions) >= 2:
                return suggestions
        except Exception as e:
            logger.error(f"[LLM] Failed to generate smart suggestions: {e}")
        
        return []

    def health_check(self) -> bool:
        """Quick health check — can we reach Groq?"""
        try:
            response = self._llm.invoke([HumanMessage(content="Hi")])
            return bool(response.content)
        except Exception:
            return False


# Singleton
llm_service = LLMService()
