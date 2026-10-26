"""
Tool definitions for the Claude API (input_schema format) plus
the Python implementations that execute against a SQLAlchemy session.
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.orm import Session

from ..models import Task, Event, Reminder


# ─── Tool Schemas (sent to Claude) ──────────────────────────────────────────

TOOLS = [
    {
        "name": "list_tasks",
        "description": "Fetch tasks from the database, optionally filtered by status, priority, or due date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "completed", "cancelled"],
                    "description": "Filter by task status."
                },
                "due_before": {
                    "type": "string",
                    "description": "ISO 8601 datetime — return tasks due before this time."
                },
                "due_after": {
                    "type": "string",
                    "description": "ISO 8601 datetime — return tasks due after this time."
                }
            },
            "required": []
        }
    },
    {
        "name": "create_task",
        "description": "Create a new task with an optional due date and priority.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title (required)."},
                "description": {"type": "string", "description": "Optional longer description."},
                "due_date": {"type": "string", "description": "ISO 8601 datetime deadline."},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority (default: medium)."
                }
            },
            "required": ["title"]
        }
    },
    {
        "name": "update_task",
        "description": "Update one or more fields of an existing task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to update."},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "due_date": {"type": "string", "description": "ISO 8601 datetime."},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "status": {"type": "string", "enum": ["open", "in_progress", "completed", "cancelled"]}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task. Always call first with confirmed=false to request user confirmation. Only call with confirmed=true after the user confirms.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to delete."},
                "confirmed": {
                    "type": "boolean",
                    "description": "Must be true to actually delete. Pass false first to get user confirmation."
                }
            },
            "required": ["task_id", "confirmed"]
        }
    },
    {
        "name": "get_events",
        "description": "Fetch calendar events, optionally filtered by a date range.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "ISO 8601 datetime — events starting after this."},
                "end": {"type": "string", "description": "ISO 8601 datetime — events starting before this."}
            },
            "required": []
        }
    },
    {
        "name": "schedule_task",
        "description": "Place a task into a calendar slot. Creates an Event linked to the task. Returns conflict error if the slot is taken.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to schedule."},
                "start": {"type": "string", "description": "ISO 8601 start datetime."},
                "end": {"type": "string", "description": "ISO 8601 end datetime."}
            },
            "required": ["task_id", "start", "end"]
        }
    },
    {
        "name": "reschedule_task",
        "description": "Move the most recent calendar event for a task to a new time slot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the task to reschedule."},
                "new_start": {"type": "string", "description": "ISO 8601 new start datetime."},
                "new_end": {"type": "string", "description": "ISO 8601 new end datetime."}
            },
            "required": ["task_id", "new_start", "new_end"]
        }
    },
    {
        "name": "set_reminder",
        "description": "Attach a reminder to a task or calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "integer", "description": "ID of the task or event."},
                "target_type": {
                    "type": "string",
                    "enum": ["task", "event"],
                    "description": "Whether the reminder is for a task or an event."
                },
                "remind_at": {"type": "string", "description": "ISO 8601 datetime when to remind."},
                "message": {"type": "string", "description": "Optional reminder message."}
            },
            "required": ["target_id", "target_type", "remind_at"]
        }
    },
    {
        "name": "find_free_slots",
        "description": "Find available time windows on a given day (9 AM–6 PM) that are not already occupied by events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "ISO date string, e.g. 2026-10-13."},
                "duration_minutes": {"type": "integer", "description": "Desired slot length in minutes."},
                "count": {"type": "integer", "description": "How many slots to return (default: 3)."}
            },
            "required": ["date", "duration_minutes"]
        }
    }
]


# ─── Python Implementations ──────────────────────────────────────────────────

def _task_to_dict(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "priority": task.priority,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


def _event_to_dict(event: Event) -> Dict[str, Any]:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
        "task_id": event.task_id,
        "created_at": event.created_at.isoformat(),
    }


def _parse_dt(s: str) -> datetime:
    """Parse an ISO 8601 string to datetime, handling trailing Z."""
    return datetime.fromisoformat(s.replace("Z", "+00:00").replace("+00:00", ""))


def tool_list_tasks(inp: Dict, db: Session) -> Dict:
    q = db.query(Task)
    if inp.get("status"):
        q = q.filter(Task.status == inp["status"])
    if inp.get("due_before"):
        q = q.filter(Task.due_date <= _parse_dt(inp["due_before"]))
    if inp.get("due_after"):
        q = q.filter(Task.due_date >= _parse_dt(inp["due_after"]))
    tasks = q.order_by(Task.created_at.desc()).all()
    return {"tasks": [_task_to_dict(t) for t in tasks], "count": len(tasks)}


def tool_create_task(inp: Dict, db: Session) -> Dict:
    if not inp.get("title"):
        return {"error": "title is required"}
    due = _parse_dt(inp["due_date"]) if inp.get("due_date") else None
    task = Task(
        title=inp["title"],
        description=inp.get("description"),
        due_date=due,
        priority=inp.get("priority", "medium"),
        status="open",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"success": True, "task": _task_to_dict(task)}


def tool_update_task(inp: Dict, db: Session) -> Dict:
    task = db.query(Task).filter(Task.id == inp["task_id"]).first()
    if not task:
        return {"error": f"Task {inp['task_id']} not found"}
    fields = ["title", "description", "priority", "status"]
    for f in fields:
        if f in inp:
            setattr(task, f, inp[f])
    if "due_date" in inp:
        task.due_date = _parse_dt(inp["due_date"]) if inp["due_date"] else None
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {"success": True, "task": _task_to_dict(task)}


def tool_delete_task(inp: Dict, db: Session) -> Dict:
    if not inp.get("confirmed", False):
        task = db.query(Task).filter(Task.id == inp["task_id"]).first()
        title = task.title if task else f"task {inp['task_id']}"
        return {
            "requires_confirmation": True,
            "task_id": inp["task_id"],
            "message": f"Are you sure you want to permanently delete '{title}'? This cannot be undone."
        }
    task = db.query(Task).filter(Task.id == inp["task_id"]).first()
    if not task:
        return {"error": f"Task {inp['task_id']} not found"}
    db.delete(task)
    db.commit()
    return {"success": True, "deleted": True, "task_id": inp["task_id"]}


def tool_get_events(inp: Dict, db: Session) -> Dict:
    q = db.query(Event)
    if inp.get("start"):
        q = q.filter(Event.end_time >= _parse_dt(inp["start"]))
    if inp.get("end"):
        q = q.filter(Event.start_time <= _parse_dt(inp["end"]))
    events = q.order_by(Event.start_time).all()
    return {"events": [_event_to_dict(e) for e in events], "count": len(events)}


def _check_event_conflict(db: Session, start: datetime, end: datetime, exclude_id: int = None) -> Event:
    q = db.query(Event).filter(Event.start_time < end, Event.end_time > start)
    if exclude_id:
        q = q.filter(Event.id != exclude_id)
    return q.first()


def tool_schedule_task(inp: Dict, db: Session) -> Dict:
    task = db.query(Task).filter(Task.id == inp["task_id"]).first()
    if not task:
        return {"error": f"Task {inp['task_id']} not found"}
    start = _parse_dt(inp["start"])
    end = _parse_dt(inp["end"])
    if end <= start:
        return {"error": "end must be after start"}
    conflict = _check_event_conflict(db, start, end)
    if conflict:
        return {
            "error": "scheduling_conflict",
            "conflict_with": _event_to_dict(conflict),
            "message": f"Time slot conflicts with '{conflict.title}' ({conflict.start_time.isoformat()}–{conflict.end_time.isoformat()})"
        }
    event = Event(title=task.title, start_time=start, end_time=end, task_id=task.id)
    db.add(event)
    # Update task status to in_progress
    task.status = "in_progress"
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    return {"success": True, "event": _event_to_dict(event)}


def tool_reschedule_task(inp: Dict, db: Session) -> Dict:
    # Find the most recent event linked to this task
    event = (
        db.query(Event)
        .filter(Event.task_id == inp["task_id"])
        .order_by(Event.created_at.desc())
        .first()
    )
    if not event:
        return {"error": f"No scheduled event found for task {inp['task_id']}"}
    new_start = _parse_dt(inp["new_start"])
    new_end = _parse_dt(inp["new_end"])
    if new_end <= new_start:
        return {"error": "new_end must be after new_start"}
    conflict = _check_event_conflict(db, new_start, new_end, exclude_id=event.id)
    if conflict:
        return {
            "error": "scheduling_conflict",
            "conflict_with": _event_to_dict(conflict),
            "message": f"New slot conflicts with '{conflict.title}'"
        }
    event.start_time = new_start
    event.end_time = new_end
    db.commit()
    db.refresh(event)
    return {"success": True, "event": _event_to_dict(event)}


def tool_set_reminder(inp: Dict, db: Session) -> Dict:
    target_type = inp.get("target_type")
    if target_type not in ("task", "event"):
        return {"error": "target_type must be 'task' or 'event'"}
    remind_at = _parse_dt(inp["remind_at"])
    task_id = inp["target_id"] if target_type == "task" else None
    event_id = inp["target_id"] if target_type == "event" else None
    reminder = Reminder(
        task_id=task_id,
        event_id=event_id,
        remind_at=remind_at,
        message=inp.get("message"),
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {
        "success": True,
        "reminder": {
            "id": reminder.id,
            "remind_at": reminder.remind_at.isoformat(),
            "message": reminder.message,
            "task_id": reminder.task_id,
            "event_id": reminder.event_id,
        }
    }


def tool_find_free_slots(inp: Dict, db: Session) -> Dict:
    date_str = inp["date"]
    duration = int(inp["duration_minutes"])
    count = int(inp.get("count", 3))

    # Parse the date
    try:
        base = datetime.fromisoformat(date_str)
    except ValueError:
        return {"error": f"Invalid date format: {date_str}"}

    day_start = base.replace(hour=9, minute=0, second=0, microsecond=0)
    day_end = base.replace(hour=18, minute=0, second=0, microsecond=0)

    # Fetch events for that day
    events = (
        db.query(Event)
        .filter(Event.start_time < day_end, Event.end_time > day_start)
        .order_by(Event.start_time)
        .all()
    )

    # Build list of busy intervals
    busy = [(e.start_time, e.end_time) for e in events]

    # Walk through the day in `duration`-minute increments
    slot_delta = timedelta(minutes=duration)
    free_slots = []
    cursor = day_start

    while cursor + slot_delta <= day_end and len(free_slots) < count:
        slot_end = cursor + slot_delta
        # Check if this slot overlaps any busy interval
        overlaps = any(b_start < slot_end and b_end > cursor for b_start, b_end in busy)
        if not overlaps:
            free_slots.append({
                "start": cursor.isoformat(),
                "end": slot_end.isoformat(),
            })
            cursor = slot_end  # advance past this slot
        else:
            cursor += timedelta(minutes=15)  # try next 15-min increment

    return {
        "date": date_str,
        "duration_minutes": duration,
        "free_slots": free_slots,
        "count": len(free_slots),
    }
