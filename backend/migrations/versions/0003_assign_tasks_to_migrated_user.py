"""D3 Task 넘기기: 주인 없는 Task를 모두 이전용 계정에 넘긴다

직접 작성한 절차다. (DATA-MIGRATION-PLAN.md 6절 D3)
- owner_id가 비어 있는 Task를 모두 이전용 계정에 넘긴다.
- 끝에서 수량 비교(전후 Task 수와 id · title · description · status가 같은지)를 하고,
  주인 없는 Task가 0건인지 확인한다. 맞지 않으면 예외로 이 리비전의 변경을 모두 취소한다.
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

MIGRATED_EMAIL = "migrated@test.com"


def _snapshot(conn):
    return conn.exec_driver_sql(
        "SELECT id, title, description, status FROM tasks ORDER BY id"
    ).fetchall()


def upgrade() -> None:
    conn = op.get_bind()

    migrated_id = conn.exec_driver_sql(
        "SELECT id FROM users WHERE email = ?", (MIGRATED_EMAIL,)
    ).scalar()
    if migrated_id is None:
        raise RuntimeError("이전용 계정이 없습니다. 이전을 멈춥니다.")

    before = _snapshot(conn)
    conn.exec_driver_sql(
        "UPDATE tasks SET owner_id = ? WHERE owner_id IS NULL", (migrated_id,)
    )
    after = _snapshot(conn)

    if after != before:
        raise RuntimeError("Task 내용이 달라졌습니다. 이 단계의 변경을 취소합니다.")
    orphans = conn.exec_driver_sql(
        "SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL"
    ).scalar()
    if orphans != 0:
        raise RuntimeError("주인 없는 Task가 남았습니다. 이 단계의 변경을 취소합니다.")
    others = conn.exec_driver_sql(
        "SELECT COUNT(*) FROM tasks WHERE owner_id != ?", (migrated_id,)
    ).scalar()
    if others != 0:
        raise RuntimeError("이전용 계정이 아닌 주인의 Task가 있습니다. 이 단계의 변경을 취소합니다.")


def downgrade() -> None:
    raise RuntimeError(
        "다운그레이드는 지원하지 않습니다. 이전 전에 만든 백업 파일로 되돌립니다."
    )
