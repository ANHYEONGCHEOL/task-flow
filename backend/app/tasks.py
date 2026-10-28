from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import User, current_user
from .db import connect
from .schemas import Status, StatusChange, Task, TaskBulkCreate, TaskCreate, TaskUpdate

# 모든 Task API는 로그인이 필요하다. 로그인하지 않으면 401이다.
router = APIRouter(
    prefix="/tasks", tags=["tasks"], dependencies=[Depends(current_user)]
)

# 기한 초과는 저장하지 않고 읽을 때 계산한다. 마감일이 오늘보다 이전이고 완료가 아니다. (BR-03)
# 자리표시자(?)가 하나 있어서 SELECT를 쓸 때 맨 앞에 "오늘"을 넘긴다.
SELECT = (
    "SELECT id, title, description, status, priority, due_date, "
    "(due_date IS NOT NULL AND due_date < ? AND status != 'DONE') AS is_overdue "
    "FROM tasks"
)
# 기한 초과 → 우선순위 HIGH부터 → 이른 마감일(없으면 맨 뒤) → 만든 순서. (BR-04)
ORDER = (
    "ORDER BY is_overdue DESC, "
    "CASE priority WHEN 'HIGH' THEN 0 WHEN 'NORMAL' THEN 1 ELSE 2 END, "
    "due_date IS NULL, due_date, id"
)
NOT_FOUND = "카드가 없습니다."


def _today() -> str:
    # "오늘"은 서버의 날짜다. (N-02)
    return date.today().isoformat()


def _not_found() -> HTTPException:
    # 남의 Task와 없는 Task는 같은 404와 같은 응답이다. 있다는 사실도 알려 주지 않는다.
    return HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)


def _get(conn, task_id: int, user_id: int):
    return conn.execute(
        f"{SELECT} WHERE id = ? AND owner_id = ?", (_today(), task_id, user_id)
    ).fetchone()


@router.get("")
def list_tasks(user: User = Depends(current_user)) -> list[Task]:
    with connect() as conn:
        rows = conn.execute(
            f"{SELECT} WHERE owner_id = ? {ORDER}", (_today(), user.id)
        ).fetchall()
    return [Task(**row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(body: TaskCreate, user: User = Depends(current_user)) -> Task:
    # 주인은 서버가 로그인한 사용자로 정한다. 요청에 owner_id가 들어 있어도 쓰지 않는다.
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, status, priority, due_date, owner_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                body.title,
                body.description,
                Status.TODO.value,
                body.priority.value,
                body.due_date,
                user.id,
            ),
        )
        row = _get(conn, cur.lastrowid, user.id)
    return Task(**row)


# AI 할일 만들기의 [모두 등록]. 한 트랜잭션이라 중간에 실패하면 하나도 저장되지 않는다.
# 입력 값은 단건 등록과 같은 규칙(TaskCreate)으로 검사한다.
@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def create_tasks_bulk(
    body: TaskBulkCreate, user: User = Depends(current_user)
) -> list[Task]:
    with connect() as conn:
        ids = [
            conn.execute(
                "INSERT INTO tasks (title, description, status, priority, due_date, owner_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.title,
                    item.description,
                    Status.TODO.value,
                    item.priority.value,
                    item.due_date,
                    user.id,
                ),
            ).lastrowid
            for item in body.items
        ]
        rows = [_get(conn, task_id, user.id) for task_id in ids]
    return [Task(**row) for row in rows]


# 상태를 바꾸는 유일한 경로다. 현재 상태와 관계없이 어느 값으로든 바꾼다. (D-005, D-009)
# 우선순위와 마감일은 바꾸지 않는다. (BR-05)
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
        row = _get(conn, task_id, user.id)
    return Task(**row)


# 보낸 필드만 바꾼다. 상태는 바뀌지 않는다. due_date에 null을 보내면 마감일을 지운다.
@router.patch("/{task_id}")
def update_task(
    task_id: int, body: TaskUpdate, user: User = Depends(current_user)
) -> Task:
    values = {
        name: getattr(body, name)
        for name in ("title", "description", "priority", "due_date")
        if name in body.model_fields_set
    }
    if "priority" in values:
        values["priority"] = values["priority"].value
    with connect() as conn:
        if values:
            # 열 이름은 위 고정 목록에서만 온다. 값은 자리표시자로 넘긴다.
            assignments = ", ".join(f"{name} = ?" for name in values)
            cur = conn.execute(
                f"UPDATE tasks SET {assignments} WHERE id = ? AND owner_id = ?",
                (*values.values(), task_id, user.id),
            )
            if cur.rowcount == 0:
                raise _not_found()
        row = _get(conn, task_id, user.id)
        if row is None:
            raise _not_found()
    return Task(**row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user: User = Depends(current_user)) -> None:
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND owner_id = ?", (task_id, user.id)
        )
        if cur.rowcount == 0:
            raise _not_found()
