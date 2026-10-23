"""D1 구조 추가: users, sessions 테이블과 tasks.owner_id 컬럼

직접 작성한 절차다. (DATA-MIGRATION-PLAN.md 6절 D1)
- users, sessions를 새로 만들고 tasks에 owner_id를 비어 있는 채로 더한다.
- 새 DB에는 tasks가 없으므로 옛 구조의 tasks를 먼저 만든다.
- 끝에서 Task가 그대로인지 확인하고, 맞지 않으면 예외로 이 리비전의 변경을 모두 취소한다.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

OLD_TASKS = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'TODO'
        CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE'))
)
"""


def _tasks_snapshot(conn):
    return conn.exec_driver_sql(
        "SELECT id, title, description, status FROM tasks ORDER BY id"
    ).fetchall()


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql(OLD_TASKS)

    columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tasks)")]
    if "owner_id" in columns:
        raise RuntimeError("tasks에 이미 owner_id가 있습니다. 이전을 멈춥니다.")
    existing = {
        row[0]
        for row in conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    if existing & {"users", "sessions"}:
        raise RuntimeError("users 또는 sessions가 이미 있습니다. 이전을 멈춥니다.")

    before = _tasks_snapshot(conn)

    conn.exec_driver_sql(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT
        )
        """
    )
    conn.exec_driver_sql(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        )
        """
    )
    conn.exec_driver_sql("ALTER TABLE tasks ADD COLUMN owner_id INTEGER")

    columns = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(tasks)")]
    if "owner_id" not in columns:
        raise RuntimeError("tasks.owner_id가 만들어지지 않았습니다.")
    if _tasks_snapshot(conn) != before:
        raise RuntimeError("Task 내용이 달라졌습니다. 이 단계의 변경을 취소합니다.")


def downgrade() -> None:
    raise RuntimeError(
        "다운그레이드는 지원하지 않습니다. 이전 전에 만든 백업 파일로 되돌립니다."
    )
