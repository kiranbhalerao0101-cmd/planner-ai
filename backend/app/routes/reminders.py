from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reminder
from ..schemas import ReminderCreate, ReminderRead

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    if not payload.task_id and not payload.event_id:
        raise HTTPException(
            status_code=400,
            detail="Either task_id or event_id must be provided"
        )
    reminder = Reminder(**payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/upcoming", response_model=List[ReminderRead])
def upcoming_reminders(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    return (
        db.query(Reminder)
        .filter(Reminder.remind_at > now, Reminder.sent == False)  # noqa: E712
        .order_by(Reminder.remind_at)
        .all()
    )
