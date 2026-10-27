import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import db_path

# alembic 리비전의 맨 끝 번호. DB가 이 번호까지 이전되어 있어야 앱이 시작한다.
HEAD_REVISION = "0005"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with conn:  # 성공하면 commit, 예외가 나면 rollback
            yield conn
    finally:
        conn.close()


def check_schema() -> None:
    """DB가 이전되어 있는지만 확인한다. 앱은 시작할 때 DB를 바꾸지 않는다."""
    with connect() as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        version = None
        if "alembic_version" in tables:
            row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
            version = row[0] if row else None
    if version != HEAD_REVISION:
        raise RuntimeError(
            "DB가 아직 이전되지 않았습니다. 백업한 뒤 backend 폴더에서 "
            "`uv run alembic upgrade head`를 실행해 주세요."
        )
