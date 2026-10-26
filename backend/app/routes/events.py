from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..schemas import EventCreate, EventUpdate, EventRead

router = APIRouter(prefix="/events", tags=["events"])


def check_conflict(db: Session, start: datetime, end: datetime, exclude_id: Optional[int] = None):
    """Return the first conflicting event, if any."""
    q = db.query(Event).filter(
        Event.start_time < end,
        Event.end_time > start,
    )
    if exclude_id is not None:
        q = q.filter(Event.id != exclude_id)
    return q.first()


@router.get("", response_model=List[EventRead])
def list_events(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if start:
        q = q.filter(Event.end_time >= start)
    if end:
        q = q.filter(Event.start_time <= end)
    return q.order_by(Event.start_time).all()


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")
    conflict = check_conflict(db, payload.start_time, payload.end_time)
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Scheduling conflict with event {conflict.id}: '{conflict.title}'"
        )
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


@router.patch("/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    # Re-check conflict after update
    conflict = check_conflict(db, event.start_time, event.end_time, exclude_id=event_id)
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Scheduling conflict with event {conflict.id}: '{conflict.title}'"
        )
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    db.delete(event)
    db.commit()
