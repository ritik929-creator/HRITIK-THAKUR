import json
import os
from datetime import datetime
from enum import Enum

import redis
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, DateTime, Integer, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/tasks")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
rdb = redis.from_url(REDIS_URL, decode_responses=True)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(engine)
app = FastAPI(title="Task Management Service", version="1.0.0")

class Status(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: Priority = Priority.medium

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None


def publish(event: str, task: Task):
    try:
        rdb.publish("task-events", json.dumps({"event": event, "task_id": task.id, "title": task.title}))
    except Exception:
        pass


def serialize(t: Task):
    return {"id": t.id, "title": t.title, "description": t.description, "status": t.status,
            "priority": t.priority, "created_at": t.created_at, "updated_at": t.updated_at}

@app.get("/health")
def health():
    return {"service": "task-service", "status": "healthy"}

@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    with Session(engine) as db:
        task = Task(title=payload.title, description=payload.description, priority=payload.priority.value)
        db.add(task); db.commit(); db.refresh(task)
        publish("task.created", task)
        return serialize(task)

@app.get("/tasks")
def list_tasks(status: Status | None = None, priority: Priority | None = None,
               search: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    with Session(engine) as db:
        stmt = select(Task)
        if status: stmt = stmt.where(Task.status == status.value)
        if priority: stmt = stmt.where(Task.priority == priority.value)
        if search: stmt = stmt.where(Task.title.ilike(f"%{search}%"))
        stmt = stmt.order_by(Task.id.desc()).offset((page - 1) * page_size).limit(page_size)
        return [serialize(t) for t in db.scalars(stmt).all()]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with Session(engine) as db:
        task = db.get(Task, task_id)
        if not task: raise HTTPException(404, "Task not found")
        return serialize(task)

@app.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    with Session(engine) as db:
        task = db.get(Task, task_id)
        if not task: raise HTTPException(404, "Task not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, key, value.value if isinstance(value, Enum) else value)
        task.updated_at = datetime.utcnow()
        db.commit(); db.refresh(task)
        publish("task.updated", task)
        return serialize(task)

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with Session(engine) as db:
        task = db.get(Task, task_id)
        if not task: raise HTTPException(404, "Task not found")
        db.delete(task); db.commit()
        try: rdb.publish("task-events", json.dumps({"event": "task.deleted", "task_id": task_id}))
        except Exception: pass
