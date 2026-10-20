from fastapi import APIRouter, HTTPException, status

from .db import connect
from .schemas import Status, StatusChange, Task, TaskCreate, TaskUpdate

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


# 상태를 바꾸는 유일한 경로다. 현재 상태와 관계없이 어느 값으로든 바꾼다. (D-005, D-009)
@router.patch("/{task_id}/status")
def change_status(task_id: int, body: StatusChange) -> Task:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?", (body.status.value, task_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "카드가 없습니다.")
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return Task(**row)


# 제목과 설명만 바꾼다. 상태는 바뀌지 않는다.
@router.patch("/{task_id}")
def update_task(task_id: int, body: TaskUpdate) -> Task:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE tasks SET title = ?, description = ? WHERE id = ?",
            (body.title, body.description, task_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "카드가 없습니다.")
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    return Task(**row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    with connect() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "카드가 없습니다.")
