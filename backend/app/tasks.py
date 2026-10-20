from fastapi import APIRouter, status

from .db import connect
from .schemas import Status, Task, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])

COLUMNS = "id, title, description, status"


@router.get("")
def list_tasks() -> list[Task]:
    with connect() as conn:
        rows = conn.execute(f"SELECT {COLUMNS} FROM tasks ORDER BY id").fetchall()
    return [Task(**row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(body: TaskCreate) -> Task:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            (body.title, body.description, Status.TODO.value),
        )
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return Task(**row)
