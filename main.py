"""A small task manager API backed by SQLite."""

import os
import sqlite3
from contextlib import asynccontextmanager, closing
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("TASKS_DB_PATH", str(BASE_DIR / "tasks.db")))


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    due_date: Optional[date] = None
    priority: Priority = Priority.medium
    status: TaskStatus = TaskStatus.todo

    model_config = ConfigDict(str_strip_whitespace=True)


class TaskPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    due_date: Optional[date] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None

    model_config = ConfigDict(str_strip_whitespace=True)


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with closing(connect()) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                due_date TEXT,
                priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
                status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'done')),
                created_at TEXT NOT NULL
            )"""
        )
        connection.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="个人任务管理器",
    version="1.0.0",
    description="记录任务、跟踪进度的轻量工具。",
    lifespan=lifespan,
)


def serialize(row: sqlite3.Row) -> dict:
    return dict(row)


@app.get("/api/tasks")
def list_tasks(
    task_status: Optional[TaskStatus] = Query(default=None, alias="status"),
    q: str = Query(default="", max_length=100),
) -> list[dict]:
    sql = "SELECT * FROM tasks WHERE 1 = 1"
    params: list[str] = []
    if task_status:
        sql += " AND status = ?"
        params.append(task_status.value)
    if q.strip():
        sql += " AND title LIKE ? COLLATE NOCASE"
        params.append(f"%{q.strip()}%")
    sql += " ORDER BY CASE status WHEN 'todo' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, due_date IS NULL, due_date, id DESC"
    with closing(connect()) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [serialize(row) for row in rows]


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int) -> dict:
    with closing(connect()) as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到这条任务。")
    return serialize(row)


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskInput) -> dict:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(connect()) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, description, due_date, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task.title, task.description, task.due_date.isoformat() if task.due_date else None,
             task.priority.value, task.status.value, now),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return serialize(row)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, changes: TaskPatch) -> dict:
    fields = changes.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="请至少修改一个字段。")
    for required_field in ("title", "description", "priority", "status"):
        if required_field in fields and fields[required_field] is None:
            raise HTTPException(status_code=422, detail=f"字段 {required_field} 不能设为空。")
    if "due_date" in fields:
        fields["due_date"] = fields["due_date"].isoformat() if fields["due_date"] else None
    for key in ("priority", "status"):
        if key in fields and fields[key] is not None:
            fields[key] = fields[key].value
    assignments = ", ".join(f"{column} = ?" for column in fields)
    values = list(fields.values()) + [task_id]
    with closing(connect()) as connection:
        cursor = connection.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="找不到这条任务。")
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return serialize(row)


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    with closing(connect()) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="找不到这条任务。")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/summary")
def task_summary() -> dict[str, int]:
    with closing(connect()) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) AS todo, "
            "SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress, "
            "SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done FROM tasks"
        ).fetchone()
    return {key: row[key] or 0 for key in ("total", "todo", "in_progress", "done")}


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
