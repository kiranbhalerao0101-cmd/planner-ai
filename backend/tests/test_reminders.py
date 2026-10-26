import pytest
from datetime import datetime, timedelta


def _future(hours=1):
    return (datetime.utcnow() + timedelta(hours=hours)).isoformat()


def _past(hours=1):
    return (datetime.utcnow() - timedelta(hours=hours)).isoformat()


def test_create_reminder_for_task(client):
    task = client.post("/api/tasks", json={"title": "Study"}).json()
    resp = client.post("/api/reminders", json={
        "task_id": task["id"],
        "remind_at": _future(2),
        "message": "Time to study!"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_id"] == task["id"]
    assert data["sent"] is False


def test_create_reminder_no_target(client):
    resp = client.post("/api/reminders", json={"remind_at": _future(1)})
    assert resp.status_code == 400


def test_upcoming_reminders(client):
    task = client.post("/api/tasks", json={"title": "Task X"}).json()
    # Create one future reminder
    client.post("/api/reminders", json={"task_id": task["id"], "remind_at": _future(1)})
    # Create one past reminder (should not appear in upcoming)
    client.post("/api/reminders", json={"task_id": task["id"], "remind_at": _past(1)})

    resp = client.get("/api/reminders/upcoming")
    assert resp.status_code == 200
    reminders = resp.json()
    assert len(reminders) == 1
    assert reminders[0]["task_id"] == task["id"]
