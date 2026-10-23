"""D2 이전용 계정 만들기

직접 작성한 절차다. (DATA-MIGRATION-PLAN.md 6절 D2, DECISIONS.md D-018)
- 기존 Task의 주인이 될 이전용 계정 migrated@test.com을 만든다.
- 이 계정은 password_hash가 비어 있어서 로그인할 수 없다. 이 이메일로 처음 가입하는
  사람이 비밀번호를 정해 계정을 받는다.
- users가 비어 있지 않으면 아무것도 바꾸지 않고 멈춘다.
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

MIGRATED_EMAIL = "migrated@test.com"


def upgrade() -> None:
    conn = op.get_bind()

    count = conn.exec_driver_sql("SELECT COUNT(*) FROM users").scalar()
    if count != 0:
        raise RuntimeError("users가 비어 있지 않습니다. 이전용 계정을 만들지 않고 멈춥니다.")

    conn.exec_driver_sql(
        "INSERT INTO users (email, password_hash) VALUES (?, NULL)", (MIGRATED_EMAIL,)
    )

    rows = conn.exec_driver_sql("SELECT email, password_hash FROM users").fetchall()
    if rows != [(MIGRATED_EMAIL, None)]:
        raise RuntimeError("users가 이전용 계정 한 명이어야 합니다. 이 단계의 변경을 취소합니다.")


def downgrade() -> None:
    raise RuntimeError(
        "다운그레이드는 지원하지 않습니다. 이전 전에 만든 백업 파일로 되돌립니다."
    )
