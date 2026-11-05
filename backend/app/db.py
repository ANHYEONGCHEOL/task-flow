from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import database_url

# alembic 리비전의 맨 끝 번호. DB가 이 번호까지 이전되어 있어야 앱이 시작한다.
HEAD_REVISION = "0001"


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    # prepare_threshold=None: Supabase Transaction pooler는 prepared statement를 쓸 수 없다.
    conn = psycopg.connect(database_url(), row_factory=dict_row, prepare_threshold=None)
    try:
        with conn:  # 성공하면 commit, 예외가 나면 rollback
            yield conn
    finally:
        conn.close()


def check_schema() -> None:
    """DB가 이전되어 있는지만 확인한다. 앱은 시작할 때 DB를 바꾸지 않는다."""
    version = None
    with connect() as conn:
        try:
            row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
            version = row["version_num"] if row else None
        except psycopg.errors.UndefinedTable:
            pass
    if version != HEAD_REVISION:
        raise RuntimeError(
            "DB가 아직 이전되지 않았습니다. 백업한 뒤 backend 폴더에서 "
            "`uv run alembic upgrade head`를 실행해 주세요."
        )
