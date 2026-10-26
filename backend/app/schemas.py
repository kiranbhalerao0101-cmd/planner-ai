from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ─── Task Schemas ────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"  # low / medium / high
    status: Optional[str] = "open"      # open / in_progress / completed / cancelled


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


# ─── Event Schemas ───────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    task_id: Optional[int] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    task_id: Optional[int] = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    task_id: Optional[int] = None
    created_at: datetime


# ─── Reminder Schemas ────────────────────────────────────────────────────────

class ReminderCreate(BaseModel):
    task_id: Optional[int] = None
    event_id: Optional[int] = None
    remind_at: datetime
    message: Optional[str] = None


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: Optional[int] = None
    event_id: Optional[int] = None
    remind_at: datetime
    message: Optional[str] = None
    sent: bool
    created_at: datetime


# ─── Chat Schemas ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ConfirmRequest(BaseModel):
    session_id: str
    confirmed: bool


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
