"""PostgreSQL 기준 스키마 (D-020)

SQLite 시절의 0001~0005를 합친 최종 구조다. 새 PostgreSQL DB를 처음 만들 때 쓴다.
- users, sessions, tasks 세 테이블.
- 기존 SQLite 데이터는 옮기지 않는다. 이전용 계정(D-018)도 만들지 않는다.
- 날짜(due_date, expires_at)는 SQLite 때와 같이 문자열(TEXT)로 둔다. API 동작을 바꾸지 않기 위해서다.
- downgrade는 만들지 않는다.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql(
        """
        CREATE TABLE users (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT
        )
        """
    )
    conn.exec_driver_sql(
        """
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        )
        """
    )
    conn.exec_driver_sql(
        """
        CREATE TABLE tasks (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'TODO'
                CHECK (status IN ('TODO', 'IN_PROGRESS', 'DONE')),
            owner_id BIGINT NOT NULL REFERENCES users(id),
            priority TEXT NOT NULL DEFAULT 'NORMAL'
                CHECK (priority IN ('LOW', 'NORMAL', 'HIGH')),
            due_date TEXT
        )
        """
    )
    conn.exec_driver_sql("CREATE INDEX tasks_owner_id_idx ON tasks (owner_id)")

    # Supabase는 public 테이블을 외부 API로도 노출한다. RLS를 켜고 정책을 만들지 않으면
    # 공개 키(anon)로는 아무것도 읽고 쓸 수 없다. 앱은 테이블 주인 역할로 직접 연결하므로
    # RLS의 영향을 받지 않는다.
    for table in ("users", "sessions", "tasks"):
        conn.exec_driver_sql(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    raise RuntimeError("다운그레이드는 지원하지 않습니다.")
