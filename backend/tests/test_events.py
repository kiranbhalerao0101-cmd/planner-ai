import pytest


SLOT_A = {"title": "Morning meeting", "start_time": "2026-10-13T09:00:00", "end_time": "2026-10-13T10:00:00"}
SLOT_B = {"title": "Afternoon review", "start_time": "2026-10-13T14:00:00", "end_time": "2026-10-13T15:00:00"}
SLOT_OVERLAP = {"title": "Overlap", "start_time": "2026-10-13T09:30:00", "end_time": "2026-10-13T10:30:00"}


def test_create_event(client):
    resp = client.post("/api/events", json=SLOT_A)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Morning meeting"
    assert "id" in data


def test_create_event_conflict(client):
    client.post("/api/events", json=SLOT_A)
    resp = client.post("/api/events", json=SLOT_OVERLAP)
    assert resp.status_code == 409
    assert "conflict" in resp.json()["detail"].lower()


def test_create_event_no_conflict_adjacent(client):
    """Events that are back-to-back (A ends when B starts) should NOT conflict."""
    client.post("/api/events", json=SLOT_A)
    adjacent = {"title": "Right after", "start_time": "2026-10-13T10:00:00", "end_time": "2026-10-13T11:00:00"}
    resp = client.post("/api/events", json=adjacent)
    assert resp.status_code == 201


def test_list_events(client):
    client.post("/api/events", json=SLOT_A)
    client.post("/api/events", json=SLOT_B)
    resp = client.get("/api/events")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_events_range(client):
    client.post("/api/events", json=SLOT_A)
    client.post("/api/events", json=SLOT_B)
    resp = client.get("/api/events?start=2026-10-13T13:00:00&end=2026-10-13T16:00:00")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["title"] == "Afternoon review"


def test_update_event(client):
    created = client.post("/api/events", json=SLOT_A).json()
    resp = client.patch(f"/api/events/{created['id']}", json={"title": "Updated meeting"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated meeting"


def test_update_event_not_self_conflict(client):
    """Updating an event's own time should not conflict with itself."""
    created = client.post("/api/events", json=SLOT_A).json()
    resp = client.patch(
        f"/api/events/{created['id']}",
        json={"start_time": "2026-10-13T09:00:00", "end_time": "2026-10-13T10:30:00"}
    )
    assert resp.status_code == 200


def test_delete_event(client):
    created = client.post("/api/events", json=SLOT_A).json()
    resp = client.delete(f"/api/events/{created['id']}")
    assert resp.status_code == 204


def test_get_event_not_found(client):
    resp = client.get("/api/events/9999")
    assert resp.status_code == 404
