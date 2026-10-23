from fastapi import APIRouter, Depends, HTTPException, status

from .auth import User, current_user
from .db import connect
from .schemas import Status, StatusChange, Task, TaskCreate, TaskUpdate

# 모든 Task API는 로그인이 필요하다. 로그인하지 않으면 401이다.
router = APIRouter(
    prefix="/tasks", tags=["tasks"], dependencies=[Depends(current_user)]
)

COLUMNS = "id, title, description, status"
NOT_FOUND = "카드가 없습니다."


def _not_found() -> HTTPException:
    # 남의 Task와 없는 Task는 같은 404와 같은 응답이다. 있다는 사실도 알려 주지 않는다.
    return HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)


@router.get("")
def list_tasks(user: User = Depends(current_user)) -> list[Task]:
    with connect() as conn:
        rows = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE owner_id = ? ORDER BY id", (user.id,)
        ).fetchall()
    return [Task(**row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(body: TaskCreate, user: User = Depends(current_user)) -> Task:
    # 주인은 서버가 로그인한 사용자로 정한다. 요청에 owner_id가 들어 있어도 쓰지 않는다.
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, status, owner_id) VALUES (?, ?, ?, ?)",
            (body.title, body.description, Status.TODO.value, user.id),
        )
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ? AND owner_id = ?",
            (cur.lastrowid, user.id),
        ).fetchone()
    return Task(**row)


# 상태를 바꾸는 유일한 경로다. 현재 상태와 관계없이 어느 값으로든 바꾼다. (D-005, D-009)
@router.patch("/{task_id}/status")
def change_status(
    task_id: int, body: StatusChange, user: User = Depends(current_user)
) -> Task:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ? AND owner_id = ?",
            (body.status.value, task_id, user.id),
        )
        if cur.rowcount == 0:
            raise _not_found()
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ? AND owner_id = ?",
            (task_id, user.id),
        ).fetchone()
    return Task(**row)


# 제목과 설명만 바꾼다. 상태는 바뀌지 않는다.
@router.patch("/{task_id}")
def update_task(
    task_id: int, body: TaskUpdate, user: User = Depends(current_user)
) -> Task:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE tasks SET title = ?, description = ? WHERE id = ? AND owner_id = ?",
            (body.title, body.description, task_id, user.id),
        )
        if cur.rowcount == 0:
            raise _not_found()
        row = conn.execute(
            f"SELECT {COLUMNS} FROM tasks WHERE id = ? AND owner_id = ?",
            (task_id, user.id),
        ).fetchone()
    return Task(**row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: User = Depends(current_user)) -> None:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND owner_id = ?", (task_id, user.id)
        )
        if cur.rowcount == 0:
            raise _not_found()
