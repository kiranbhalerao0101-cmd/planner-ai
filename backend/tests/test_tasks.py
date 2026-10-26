import pytest


def test_create_task(client):
    resp = client.post("/api/tasks", json={"title": "Buy groceries", "priority": "high"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Buy groceries"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert "id" in data


def test_create_task_missing_title(client):
    resp = client.post("/api/tasks", json={"description": "No title here"})
    assert resp.status_code == 422


def test_list_tasks_empty(client):
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks(client):
    client.post("/api/tasks", json={"title": "Task A"})
    client.post("/api/tasks", json={"title": "Task B", "status": "completed"})
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_tasks_filter_status(client):
    client.post("/api/tasks", json={"title": "Open task"})
    client.post("/api/tasks", json={"title": "Done task", "status": "completed"})
    resp = client.get("/api/tasks?status=open")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Open task"


def test_get_task(client):
    created = client.post("/api/tasks", json={"title": "My task"}).json()
    resp = client.get(f"/api/tasks/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "My task"


def test_get_task_not_found(client):
    resp = client.get("/api/tasks/9999")
    assert resp.status_code == 404


def test_update_task(client):
    created = client.post("/api/tasks", json={"title": "Old title"}).json()
    resp = client.patch(f"/api/tasks/{created['id']}", json={"title": "New title", "status": "completed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New title"
    assert data["status"] == "completed"


def test_update_task_not_found(client):
    resp = client.patch("/api/tasks/9999", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_task(client):
    created = client.post("/api/tasks", json={"title": "Delete me"}).json()
    resp = client.delete(f"/api/tasks/{created['id']}")
    assert resp.status_code == 204
    # Confirm it's gone
    resp2 = client.get(f"/api/tasks/{created['id']}")
    assert resp2.status_code == 404


def test_delete_task_not_found(client):
    resp = client.delete("/api/tasks/9999")
    assert resp.status_code == 404
