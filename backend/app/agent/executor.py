"""
Maps tool names from Claude API responses to their Python implementations.
"""

from typing import Any, Dict
from sqlalchemy.orm import Session

from .tools import (
    tool_list_tasks,
    tool_create_task,
    tool_update_task,
    tool_delete_task,
    tool_get_events,
    tool_schedule_task,
    tool_reschedule_task,
    tool_set_reminder,
    tool_find_free_slots,
)

TOOL_MAP = {
    "list_tasks": tool_list_tasks,
    "create_task": tool_create_task,
    "update_task": tool_update_task,
    "delete_task": tool_delete_task,
    "get_events": tool_get_events,
    "schedule_task": tool_schedule_task,
    "reschedule_task": tool_reschedule_task,
    "set_reminder": tool_set_reminder,
    "find_free_slots": tool_find_free_slots,
}


def execute_tool(tool_name: str, tool_input: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Dispatch a tool call to its implementation.
    Returns a dict that is safe to serialize as JSON.
    """
    fn = TOOL_MAP.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return fn(tool_input, db)
    except Exception as exc:
        return {"error": f"Tool execution failed: {str(exc)}"}
