"""우선순위와 마감일 열 추가 (#21, DATA-MODEL.md priority · due_date)

- priority: NOT NULL, 기본값 NORMAL, LOW · NORMAL · HIGH만 허용. 이미 있는 Task는 NORMAL이 된다.
- due_date: 비울 수 있다. 이미 있는 Task는 마감일 없음이 된다.
- ADD COLUMN만 쓴다. tasks를 다시 만들지 않으므로 id 번호(sqlite_sequence)와
  owner_id의 NOT NULL · 외래 키는 그대로 남는다.
- 끝에서 Task의 기존 내용이 그대로인지 확인하고, 맞지 않으면 예외로 이 리비전의 변경을 취소한다.
- downgrade는 만들지 않는다. 되돌리기는 이전 전에 만든 백업 파일로 한다.
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _snapshot(conn):
    return conn.exec_driver_sql(
        "SELECT id, title, description, status, owner_id FROM tasks ORDER BY id"
    ).fetchall()


def upgrade() -> None:
    conn = op.get_bind()
    before = _snapshot(conn)

    conn.exec_driver_sql(
        "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'NORMAL' "
        "CHECK (priority IN ('LOW', 'NORMAL', 'HIGH'))"
    )
    conn.exec_driver_sql("ALTER TABLE tasks ADD COLUMN due_date TEXT")

    if _snapshot(conn) != before:
        raise RuntimeError("Task 내용이 달라졌습니다. 이 단계의 변경을 취소합니다.")
    violations = conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError("외래 키 위반이 있습니다. 이 단계의 변경을 취소합니다.")
