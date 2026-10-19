from fastapi.testclient import TestClient

import main


def test_task_workflow_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.db")
    with TestClient(main.app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/docs").status_code == 200
        created = client.post("/api/tasks", json={
            "title": "整理桌面", "description": "清理下载文件夹", "due_date": "2026-11-01",
            "priority": "high", "status": "todo",
        })
        assert created.status_code == 201
        task = created.json()
        assert task["title"] == "整理桌面"
        assert task["created_at"]
        assert client.get(f"/api/tasks/{task['id']}").json()["title"] == "整理桌面"

        updated = client.patch(f"/api/tasks/{task['id']}", json={"status": "in_progress"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "in_progress"

        assert client.get("/api/tasks", params={"q": "桌面"}).json()[0]["id"] == task["id"]
        assert len(client.get("/api/tasks", params={"status": "in_progress"}).json()) == 1
        assert client.get("/api/summary").json() == {"total": 1, "todo": 0, "in_progress": 1, "done": 0}

        listed_again = client.get("/api/tasks").json()
        assert listed_again[0]["id"] == task["id"]
        assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
        assert client.get("/api/tasks").json() == []


def test_validation_and_missing_task(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.db")
    with TestClient(main.app) as client:
        assert client.post("/api/tasks", json={"title": "   "}).status_code == 422
        assert client.post("/api/tasks", json={"title": "有效", "priority": "urgent"}).status_code == 422
        assert client.patch("/api/tasks/99", json={"status": "done"}).status_code == 404
        assert client.delete("/api/tasks/99").status_code == 404
        assert client.patch("/api/tasks/99", json={}).status_code == 400
