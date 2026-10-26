"""
Agent tool and loop tests.
All Anthropic API calls are mocked — no real API key required.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.agent.tools import (
    tool_list_tasks, tool_create_task, tool_update_task, tool_delete_task,
    tool_get_events, tool_schedule_task, tool_reschedule_task,
    tool_set_reminder, tool_find_free_slots,
)
from app.agent.executor import execute_tool
from app.models import Task, Event


# ─── Test DB fixture ─────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ─── Tool: list_tasks ────────────────────────────────────────────────────────

def test_list_tasks_empty(db):
    result = tool_list_tasks({}, db)
    assert result["count"] == 0
    assert result["tasks"] == []


def test_list_tasks_filter(db):
    tool_create_task({"title": "Open task"}, db)
    tool_create_task({"title": "Done task", "priority": "high"}, db)
    # update second task
    tasks = tool_list_tasks({}, db)["tasks"]
    tool_update_task({"task_id": tasks[1]["id"], "status": "completed"}, db)
    result = tool_list_tasks({"status": "open"}, db)
    assert result["count"] == 1


# ─── Tool: create_task ───────────────────────────────────────────────────────

def test_create_task_success(db):
    result = tool_create_task({"title": "Test task", "priority": "high"}, db)
    assert result["success"] is True
    assert result["task"]["title"] == "Test task"


def test_create_task_missing_title(db):
    result = tool_create_task({}, db)
    assert "error" in result


# ─── Tool: update_task ───────────────────────────────────────────────────────

def test_update_task_success(db):
    created = tool_create_task({"title": "Old"}, db)["task"]
    result = tool_update_task({"task_id": created["id"], "title": "New", "status": "completed"}, db)
    assert result["success"] is True
    assert result["task"]["title"] == "New"
    assert result["task"]["status"] == "completed"


def test_update_task_not_found(db):
    result = tool_update_task({"task_id": 9999, "title": "x"}, db)
    assert "error" in result


# ─── Tool: delete_task ───────────────────────────────────────────────────────

def test_delete_task_requires_confirmation(db):
    created = tool_create_task({"title": "Temp"}, db)["task"]
    result = tool_delete_task({"task_id": created["id"], "confirmed": False}, db)
    assert result["requires_confirmation"] is True


def test_delete_task_confirmed(db):
    created = tool_create_task({"title": "Temp"}, db)["task"]
    result = tool_delete_task({"task_id": created["id"], "confirmed": True}, db)
    assert result["success"] is True
    assert result["deleted"] is True
    # Verify gone
    remaining = tool_list_tasks({}, db)
    assert remaining["count"] == 0


def test_delete_task_not_found(db):
    result = tool_delete_task({"task_id": 9999, "confirmed": True}, db)
    assert "error" in result


# ─── Tool: get_events ────────────────────────────────────────────────────────

def test_get_events_empty(db):
    result = tool_get_events({}, db)
    assert result["count"] == 0


# ─── Tool: schedule_task ─────────────────────────────────────────────────────

def test_schedule_task_success(db):
    task = tool_create_task({"title": "Write report"}, db)["task"]
    result = tool_schedule_task({
        "task_id": task["id"],
        "start": "2026-10-13T10:00:00",
        "end": "2026-10-13T11:00:00",
    }, db)
    assert result["success"] is True
    assert result["event"]["task_id"] == task["id"]


def test_schedule_task_conflict(db):
    task1 = tool_create_task({"title": "Task 1"}, db)["task"]
    task2 = tool_create_task({"title": "Task 2"}, db)["task"]
    tool_schedule_task({"task_id": task1["id"], "start": "2026-10-13T10:00:00", "end": "2026-10-13T11:00:00"}, db)
    result = tool_schedule_task({"task_id": task2["id"], "start": "2026-10-13T10:30:00", "end": "2026-10-13T11:30:00"}, db)
    assert result.get("error") == "scheduling_conflict"


def test_schedule_task_not_found(db):
    result = tool_schedule_task({"task_id": 9999, "start": "2026-10-13T10:00:00", "end": "2026-10-13T11:00:00"}, db)
    assert "error" in result


# ─── Tool: reschedule_task ───────────────────────────────────────────────────

def test_reschedule_task_success(db):
    task = tool_create_task({"title": "Meeting"}, db)["task"]
    tool_schedule_task({"task_id": task["id"], "start": "2026-10-13T09:00:00", "end": "2026-10-13T10:00:00"}, db)
    result = tool_reschedule_task({
        "task_id": task["id"],
        "new_start": "2026-10-13T14:00:00",
        "new_end": "2026-10-13T15:00:00",
    }, db)
    assert result["success"] is True
    assert "14:00" in result["event"]["start_time"]


def test_reschedule_task_no_event(db):
    task = tool_create_task({"title": "Unscheduled"}, db)["task"]
    result = tool_reschedule_task({"task_id": task["id"], "new_start": "2026-10-13T10:00:00", "new_end": "2026-10-13T11:00:00"}, db)
    assert "error" in result


# ─── Tool: set_reminder ──────────────────────────────────────────────────────

def test_set_reminder_for_task(db):
    task = tool_create_task({"title": "Exam"}, db)["task"]
    result = tool_set_reminder({
        "target_id": task["id"],
        "target_type": "task",
        "remind_at": "2026-10-13T08:00:00",
        "message": "Don't forget!"
    }, db)
    assert result["success"] is True
    assert result["reminder"]["task_id"] == task["id"]


def test_set_reminder_invalid_type(db):
    result = tool_set_reminder({"target_id": 1, "target_type": "invalid", "remind_at": "2026-10-13T08:00:00"}, db)
    assert "error" in result


# ─── Tool: find_free_slots ───────────────────────────────────────────────────

def test_find_free_slots_empty_day(db):
    result = tool_find_free_slots({"date": "2026-10-15", "duration_minutes": 60}, db)
    assert result["count"] > 0
    assert len(result["free_slots"]) > 0


def test_find_free_slots_with_events(db):
    # Fill 9–17 with events
    for hour in range(9, 17):
        event = Event(
            title=f"Block {hour}",
            start_time=__import__('datetime').datetime(2026, 10, 15, hour, 0),
            end_time=__import__('datetime').datetime(2026, 10, 15, hour + 1, 0),
        )
        db.add(event)
    db.commit()
    result = tool_find_free_slots({"date": "2026-10-15", "duration_minutes": 60, "count": 3}, db)
    # Only 17:00–18:00 is free
    assert result["count"] <= 1


# ─── Executor ────────────────────────────────────────────────────────────────

def test_executor_unknown_tool(db):
    result = execute_tool("nonexistent_tool", {}, db)
    assert "error" in result


def test_executor_dispatches_correctly(db):
    result = execute_tool("list_tasks", {}, db)
    assert "tasks" in result


# ─── Agent Loop (mocked Anthropic) ───────────────────────────────────────────

import asyncio
from app.agent.loop import run_agent_loop, conversation_history, pending_confirmations


def _collect(gen):
    """Run async generator and collect all events."""
    async def _inner():
        events = []
        async for e in gen:
            events.append(e)
        return events
    return asyncio.run(_inner())


def _make_mock_response(text="All done!", stop_reason="end_turn"):
    mock_block = MagicMock()
    mock_block.type = "text"
    mock_block.text = text
    resp = MagicMock()
    resp.content = [mock_block]
    resp.stop_reason = stop_reason
    return resp


def _make_tool_use_response(tool_name, tool_input, tool_use_id="tu_1"):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_use_id
    resp = MagicMock()
    resp.content = [tool_block]
    resp.stop_reason = "tool_use"
    return resp


def test_agent_loop_text_only(db):
    conversation_history.clear()
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_mock_response("Hello!")

    with patch("app.agent.loop._get_client", return_value=mock_client), \
         patch("app.agent.loop.settings") as mock_settings:
        mock_settings.anthropic_api_key = "sk-test"
        mock_settings.max_agent_steps = 8
        mock_settings.model = "claude-test"
        events = _collect(run_agent_loop("sess1", "Hi", db))

    types = [e["type"] for e in events]
    assert "message_start" in types
    assert "text" in types
    assert "done" in types


def test_agent_loop_tool_call(db):
    conversation_history.clear()
    mock_client = MagicMock()
    # First call: tool_use, second call: end_turn text
    mock_client.messages.create.side_effect = [
        _make_tool_use_response("list_tasks", {}, "tu_1"),
        _make_mock_response("You have 0 tasks."),
    ]

    with patch("app.agent.loop._get_client", return_value=mock_client), \
         patch("app.agent.loop.settings") as mock_settings:
        mock_settings.anthropic_api_key = "sk-test"
        mock_settings.max_agent_steps = 8
        mock_settings.model = "claude-test"
        events = _collect(run_agent_loop("sess2", "List tasks", db))

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    assert "done" in types


def test_agent_loop_confirmation_required(db):
    conversation_history.clear()
    pending_confirmations.clear()
    task = tool_create_task({"title": "Delete me"}, db)["task"]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_tool_use_response(
        "delete_task", {"task_id": task["id"], "confirmed": False}, "tu_del"
    )

    with patch("app.agent.loop._get_client", return_value=mock_client), \
         patch("app.agent.loop.settings") as mock_settings:
        mock_settings.anthropic_api_key = "sk-test"
        mock_settings.max_agent_steps = 8
        mock_settings.model = "claude-test"
        events = _collect(run_agent_loop("sess3", "Delete task", db))

    types = [e["type"] for e in events]
    assert "confirmation_required" in types
    assert "done" in types


def test_agent_loop_max_steps_guard(db):
    """Loop should terminate after max_agent_steps even if model keeps returning tool_use."""
    conversation_history.clear()
    mock_client = MagicMock()
    # Always return tool_use — should terminate after MAX steps
    mock_client.messages.create.return_value = _make_tool_use_response("list_tasks", {})

    with patch("app.agent.loop._get_client", return_value=mock_client), \
         patch("app.agent.loop.settings") as mock_settings:
        mock_settings.anthropic_api_key = "sk-test"
        mock_settings.max_agent_steps = 3
        mock_settings.model = "claude-test"
        events = _collect(run_agent_loop("sess4", "Loop forever", db))

    assert events[-1]["type"] == "done"
    tool_calls = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_calls) <= 3


def test_agent_loop_missing_api_key(db):
    conversation_history.clear()
    with patch("app.agent.loop.settings") as mock_settings:
        mock_settings.anthropic_api_key = ""
        mock_settings.max_agent_steps = 8
        events = _collect(run_agent_loop("sess5", "Hello", db))
    types = [e["type"] for e in events]
    assert "error" in types
    assert "done" in types
