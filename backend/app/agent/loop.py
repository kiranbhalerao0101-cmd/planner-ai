"""
Agent loop using Groq API (OpenAI-compatible) with tool/function calling.
Uses httpx directly — no extra package required.
"""

import json
import logging
import httpx
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.orm import Session

from ..config import settings
from .tools import TOOLS
from .executor import execute_tool
from .prompts import get_system_prompt

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# In-memory session stores
conversation_history: Dict[str, List[Dict]] = {}
pending_confirmations: Dict[str, Dict] = {}


def _build_groq_tools() -> list:
    """Convert our tool definitions to OpenAI/Groq function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        }
        for tool in TOOLS
    ]


def _call_groq(messages: list) -> dict:
    """Make a Groq API call and return parsed JSON."""
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.model,
        "messages": messages,
        "tools": _build_groq_tools(),
        "tool_choice": "auto",
        "max_tokens": 4096,
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(GROQ_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Groq API error {resp.status_code}: {resp.text[:400]}")
    return resp.json()


async def run_agent_loop(
    session_id: str,
    user_message: str,
    db: Session,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Async generator driving the Groq tool-calling loop."""

    if not settings.groq_api_key:
        yield {"type": "error", "message": "GROQ_API_KEY is not configured. Add it to backend/.env and restart."}
        yield {"type": "done"}
        return

    if session_id not in conversation_history:
        conversation_history[session_id] = []

    history = conversation_history[session_id]

    # Build messages: system + history + new user message
    messages = [{"role": "system", "content": get_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Save user message to history
    history.append({"role": "user", "content": user_message})

    yield {"type": "message_start"}

    step = 0
    while step < settings.max_agent_steps:
        step += 1

        try:
            response = _call_groq(messages)
        except Exception as exc:
            yield {"type": "error", "message": str(exc)}
            break

        choice = response.get("choices", [{}])[0]
        msg = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        # Emit text content
        if msg.get("content"):
            yield {"type": "text", "content": msg["content"]}

        # Add assistant message to messages list
        messages.append(msg)

        # No tool calls — we're done
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            break

        # Execute each tool call
        tool_results = []
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            try:
                tool_input = json.loads(tc["function"].get("arguments", "{}"))
            except json.JSONDecodeError:
                tool_input = {}

            yield {"type": "tool_call", "name": tool_name, "input": tool_input}

            result = execute_tool(tool_name, tool_input, db)

            yield {"type": "tool_result", "name": tool_name, "result": result}

            # Confirmation required?
            if result.get("requires_confirmation"):
                pending_confirmations[session_id] = {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_call_id": tc["id"],
                    "messages": list(messages),
                    "history": list(history),
                }
                yield {
                    "type": "confirmation_required",
                    "tool": tool_name,
                    "task_id": result.get("task_id"),
                    "message": result.get("message", "This action requires your confirmation."),
                }
                yield {"type": "done"}
                return

            tool_results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })

        # Add tool results to messages and loop again
        messages.extend(tool_results)

    # Save final assistant reply to history
    final_msg = messages[-1] if messages else {}
    if final_msg.get("role") == "assistant":
        history.append(final_msg)

    yield {"type": "done"}


async def resume_after_confirmation(
    session_id: str,
    confirmed: bool,
    db: Session,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Resume after a confirmation_required event."""
    pending = pending_confirmations.pop(session_id, None)
    if not pending:
        yield {"type": "error", "message": "No pending confirmation for this session."}
        yield {"type": "done"}
        return

    if not confirmed:
        yield {"type": "text", "content": "Action cancelled. The task was not deleted."}
        yield {"type": "done"}
        return

    tool_name = pending["tool_name"]
    tool_input = dict(pending["tool_input"])
    tool_input["confirmed"] = True
    messages = pending["messages"]
    history = pending["history"]

    yield {"type": "message_start"}
    yield {"type": "tool_call", "name": tool_name, "input": tool_input}

    result = execute_tool(tool_name, tool_input, db)
    yield {"type": "tool_result", "name": tool_name, "result": result}

    # Add confirmed tool result and get Groq's summary
    messages.append({
        "role": "tool",
        "tool_call_id": pending["tool_call_id"],
        "content": json.dumps(result, default=str),
    })

    try:
        response = _call_groq(messages)
        choice = response.get("choices", [{}])[0]
        msg = choice.get("message", {})
        if msg.get("content"):
            yield {"type": "text", "content": msg["content"]}
        history.append(msg)
    except Exception:
        yield {"type": "text", "content": "Task deleted successfully." if result.get("deleted") else "Action completed."}

    conversation_history[session_id] = history
    yield {"type": "done"}
