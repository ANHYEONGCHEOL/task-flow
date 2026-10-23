"""D4 NOT NULL과 외래 키 적용

직접 작성한 절차다. (DATA-MIGRATION-PLAN.md 6절 D4, owner_id는 NOT NULL이고 users.id를 가리킨다)
- SQLite는 컬럼의 제약을 바로 바꿀 수 없어서 새 tasks를 만들어 복사하고 바꾼다.
- 끝에서 Task 수와 내용이 그대로인지, 외래 키 위반이 없는지(foreign_key_check) 확인하고,
  맞지 않으면 예외로 이 리비전의 변경을 모두 취소한다.
- AUTOINCREMENT 번호(sqlite_sequence)는 옛 값을 그대로 이어 간다.
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _snapshot(conn):
    return conn.exec_driver_sql(
        "SELECT id, title, description, status, owner_id FROM tasks ORDER BY id"
    ).fetchall()


def upgrade() -> None:
    conn = op.get_bind()

    orphans = conn.exec_driver_sql(
        "SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL"
    ).scalar()
    if orphans != 0:
        raise RuntimeError("주인 없는 Task가 있어 NOT NULL을 적용할 수 없습니다. 멈춥니다.")

    before = _snapshot(conn)
    old_seq = conn.exec_driver_sql(
        "SELECT seq FROM sqlite_sequence WHERE name = 'tasks'"
    ).scalar()

    conn.exec_driver_sql(
        """
        CREATE TABLE tasks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'TODO'
                CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
            owner_id INTEGER NOT NULL REFERENCES users(id)
        )
        """
    )
    conn.exec_driver_sql(
        "INSERT INTO tasks_new (id, title, description, status, owner_id) "
        "SELECT id, title, description, status, owner_id FROM tasks"
    )
    conn.exec_driver_sql("DROP TABLE tasks")
    conn.exec_driver_sql("ALTER TABLE tasks_new RENAME TO tasks")
    if old_seq is not None:
        conn.exec_driver_sql(
            "UPDATE sqlite_sequence SET seq = ? WHERE name = 'tasks'", (old_seq,)
        )

    if _snapshot(conn) != before:
        raise RuntimeError("Task 내용이 달라졌습니다. 이 단계의 변경을 취소합니다.")
    violations = conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise RuntimeError("외래 키 위반이 있습니다. 이 단계의 변경을 취소합니다.")


def downgrade() -> None:
    raise RuntimeError(
        "다운그레이드는 지원하지 않습니다. 이전 전에 만든 백업 파일로 되돌립니다."
    )
